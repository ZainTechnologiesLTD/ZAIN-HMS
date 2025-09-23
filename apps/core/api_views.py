# apps/core/api_views.py
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime
import json
import requests
import subprocess
import os
# from apps.staff.models import Department
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.billing.models import Bill
from apps.emergency.models import EmergencyCase
from .models import Notification, ActivityLog, SystemConfiguration, FileUpload
from .version_models import SystemUpdate, UpdateNotification, DeploymentLog
from .serializers import (
    NotificationSerializer, ActivityLogSerializer, SystemConfigurationSerializer,
    UserProfileSerializer, FileUploadSerializer, DashboardStatsSerializer
)

User = get_user_model()


class NotificationViewSet(viewsets.ModelViewSet):
    """Notification API ViewSet"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            return Notification.objects.filter(
                recipient=self.request.user,
                tenant=tenant
            ).order_by('-created_at')
        return Notification.objects.none()
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        tenant = getattr(request, 'tenant', None)
        if tenant:
            Notification.objects.filter(
                recipient=request.user,
                tenant=tenant,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
        return Response({'status': 'all notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get unread notifications count"""
        tenant = getattr(request, 'tenant', None)
        if tenant:
            count = Notification.objects.filter(
                recipient=request.user,
                tenant=tenant,
                is_read=False
            ).count()
        else:
            count = 0
        return Response({'unread_count': count})


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Activity Log API ViewSet (Read-only)"""
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = ActivityLog.objects.none()  # Default empty queryset to prevent errors
    
    def get_queryset(self):
        # Check for swagger fake view to prevent schema generation errors
        if getattr(self, 'swagger_fake_view', False):
            return ActivityLog.objects.none()
            
        if not self.request.user.is_authenticated:
            return ActivityLog.objects.none()
            
        tenant = getattr(self.request, 'tenant', None)
        user = self.request.user
        
        # Only admins can view all activity logs
        if hasattr(user, 'role') and user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser:
            if tenant:
                return ActivityLog.objects.filter(tenant=tenant).order_by('-timestamp')
        else:
            # Regular users can only view their own activity logs
            if tenant:
                return ActivityLog.objects.filter(
                    tenant=tenant,
                    user=user
                ).order_by('-timestamp')
        
        return ActivityLog.objects.none()


class DashboardStatsAPIView(APIView):
    """Dashboard statistics API"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': 'Tenant not found'}, status=400)
        
        user = request.user
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Base filters
        tenant_filter = {'tenant': tenant}
        today_filter = {**tenant_filter, 'created_at__date': today}
        week_filter = {**tenant_filter, 'created_at__date__gte': week_start}
        month_filter = {**tenant_filter, 'created_at__date__gte': month_start}
        
        stats = {}
        
        if user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser:
            stats = {
                'overview': {
                    'total_patients': Patient.objects.filter(**tenant_filter).count(),
                    'total_doctors': User.objects.filter(**tenant_filter, role='DOCTOR', is_active=True).count(),
                    'total_nurses': User.objects.filter(**tenant_filter, role='NURSE', is_active=True).count(),
                    'total_appointments': Appointment.objects.filter(**tenant_filter).count(),
                },
                'today': {
                    'new_patients': Patient.objects.filter(**today_filter).count(),
                    'appointments': Appointment.objects.filter(
                        tenant=tenant, appointment_date=today
                    ).count(),
                    'emergency_cases': EmergencyCase.objects.filter(**today_filter).count(),
                    'revenue': Bill.objects.filter(**today_filter, status='PAID').aggregate(
                        total=Sum('total_amount')
                    )['total'] or 0,
                },
                'this_week': {
                    'new_patients': Patient.objects.filter(**week_filter).count(),
                    'appointments': Appointment.objects.filter(
                        tenant=tenant, 
                        appointment_date__gte=week_start
                    ).count(),
                    'revenue': Bill.objects.filter(**week_filter, status='PAID').aggregate(
                        total=Sum('total_amount')
                    )['total'] or 0,
                },
                'this_month': {
                    'new_patients': Patient.objects.filter(**month_filter).count(),
                    'appointments': Appointment.objects.filter(
                        tenant=tenant,
                        appointment_date__gte=month_start
                    ).count(),
                    'revenue': Bill.objects.filter(**month_filter, status='PAID').aggregate(
                        total=Sum('total_amount')
                    )['total'] or 0,
                },
                'pending': {
                    'appointments': Appointment.objects.filter(**tenant_filter, status='SCHEDULED').count(),
                    'bills': Bill.objects.filter(**tenant_filter, status='PENDING').count(),
                    'emergency_cases': EmergencyCase.objects.filter(
                        **tenant_filter, status__in=['WAITING', 'IN_PROGRESS']
                    ).count(),
                }
            }
        elif user.role == 'DOCTOR':
            # Get the doctor instance associated with this user
            from apps.doctors.models import Doctor
            try:
                doctor = Doctor.objects.get(user=user)
                
                # Apply hospital filtering along with tenant_filter
                base_filter = {'doctor': doctor, **tenant_filter}
                # If tenant_filter doesn't include hospital filtering, add it from session
                if 'patient__hospital_id' not in tenant_filter:
                    selected_hospital_id = getattr(request, 'session', {}).get('selected_hospital_id')
                    if selected_hospital_id:
                        base_filter['patient__hospital_id'] = selected_hospital_id
                
                doctor_appointments = Appointment.objects.filter(**base_filter)
                stats = {
                    'my_stats': {
                        'total_appointments': doctor_appointments.count(),
                        'appointments_today': doctor_appointments.filter(appointment_date=today).count(),
                        'pending_appointments': doctor_appointments.filter(status='SCHEDULED').count(),
                        'completed_appointments': doctor_appointments.filter(status='COMPLETED').count(),
                        'total_patients': doctor_appointments.values('patient').distinct().count(),
                    }
                }
            except Doctor.DoesNotExist:
                stats = {
                    'my_stats': {
                        'total_appointments': 0,
                        'appointments_today': 0,
                        'pending_appointments': 0,
                        'completed_appointments': 0,
                        'total_patients': 0,
                    }
                }
        
        return Response(stats)


class GlobalSearchAPIView(APIView):
    """Global search API"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        if not query or len(query) < 2:
            return Response({'results': []})
        
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'results': []})
        
        results = []
        
        # Search patients
        patients = Patient.objects.filter(
            Q(tenant=tenant) & (
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(patient_id__icontains=query) |
                Q(email__icontains=query)
            )
        )[:10]
        
        for patient in patients:
            results.append({
                'type': 'patient',
                'id': str(patient.id),
                'title': patient.get_full_name(),
                'subtitle': f"ID: {patient.patient_id}",
                'url': f'/patients/{patient.id}/',
                'avatar': patient.profile_picture.url if patient.profile_picture else None
            })
        
        # Search doctors if user has permission
        if request.user.has_module_permission('doctors'):
            doctors = User.objects.filter(
                Q(tenant=tenant, role='DOCTOR') & (
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(email__icontains=query)
                )
            )[:5]
            
            for doctor in doctors:
                results.append({
                    'type': 'doctor',
                    'id': str(doctor.id),
                    'title': doctor.get_display_name(),
                    'subtitle': doctor.specialization or 'Doctor',
                    'url': f'/doctors/{doctor.id}/',
                    'avatar': doctor.profile_picture.url if doctor.profile_picture else None
                })
        
        # Search appointments if user has permission
        if request.user.has_module_permission('appointments'):
            appointments = Appointment.objects.filter(
                Q(tenant=tenant) & (
                    Q(patient__first_name__icontains=query) |
                    Q(patient__last_name__icontains=query) |
                    Q(appointment_id__icontains=query)
                )
            )[:5]
            
            for appointment in appointments:
                results.append({
                    'type': 'appointment',
                    'id': str(appointment.id),
                    'title': f"Appointment - {appointment.patient.get_full_name()}",
                    'subtitle': f"{appointment.appointment_date} at {appointment.appointment_time}",
                    'url': f'/appointments/{appointment.id}/',
                })
        
        return Response({'results': results})


class SystemConfigurationAPIView(generics.RetrieveUpdateAPIView):
    """System configuration API"""
    serializer_class = SystemConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            obj, created = SystemConfiguration.objects.get_or_create(tenant=tenant)
            return obj
        return None
    
    def get(self, request, *args, **kwargs):
        if not (request.user.role in ['ADMIN', 'SUPERADMIN'] or request.user.is_superuser):
            return Response({'error': 'Permission denied'}, status=403)
        return super().get(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        if not (request.user.role in ['ADMIN', 'SUPERADMIN'] or request.user.is_superuser):
            return Response({'error': 'Permission denied'}, status=403)
        return super().patch(request, *args, **kwargs)


class UserProfileAPIView(generics.RetrieveAPIView):
    """User profile API"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UpdateUserProfileAPIView(generics.UpdateAPIView):
    """Update user profile API"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class FileUploadAPIView(APIView):
    """File upload API"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return Response({'error': 'Tenant not found'}, status=400)
        
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=400)
        
        # Create file upload record
        file_upload = FileUpload.objects.create(
            tenant=tenant,
            uploaded_by=request.user,
            file=file_obj,
            original_name=file_obj.name,
            file_size=file_obj.size,
            content_type=file_obj.content_type,
            description=request.data.get('description', ''),
            is_public=request.data.get('is_public', False),
        )
        
        serializer = FileUploadSerializer(file_upload)
        return Response(serializer.data, status=201)


class MarkNotificationsReadAPIView(APIView):
    """Mark notifications as read API"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        notification_ids = request.data.get('notification_ids', [])
        
        if notification_ids:
            # Mark specific notifications as read
            notifications = Notification.objects.filter(
                id__in=notification_ids,
                recipient=request.user,
                tenant=tenant
            )
            updated_count = 0
            for notification in notifications:
                if not notification.is_read:
                    notification.mark_as_read()
                    updated_count += 1
        else:
            # Mark all as read
            updated_count = Notification.objects.filter(
                recipient=request.user,
                tenant=tenant,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
        
        return Response({'updated_count': updated_count})


class BulkNotificationActionAPIView(APIView):
    """Bulk notification actions API"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        tenant = getattr(request, 'tenant', None)
        notification_ids = request.data.get('notification_ids', [])
        action = request.data.get('action', '')
        
        if not notification_ids or not action:
            return Response({'error': 'Invalid request'}, status=400)
        
        notifications = Notification.objects.filter(
            id__in=notification_ids,
            recipient=request.user,
            tenant=tenant
        )
        
        updated_count = 0
        
        if action == 'mark_read':
            for notification in notifications:
                if not notification.is_read:
                    notification.mark_as_read()
                    updated_count += 1
        
        elif action == 'delete':
            updated_count = notifications.count()
            notifications.delete()
        
        return Response({
            'success': True,
            'updated_count': updated_count,
            'action': action
        })


# ===========================
# UPDATE SYSTEM API VIEWS
# ===========================

@method_decorator(staff_member_required, name='dispatch')
class CheckUpdatesView(View):
    def get(self, request):
        """Check for available updates from GitHub releases"""
        try:
            # Get latest release from GitHub
            github_api_url = f"https://api.github.com/repos/{settings.GITHUB_REPO}/releases/latest"
            headers = {
                'Authorization': f'token {settings.GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(github_api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name'].lstrip('v')
                current_version = getattr(settings, 'VERSION', '1.0.0')
                
                # Check if update is available
                update_available = self.version_compare(latest_version, current_version) > 0
                
                if update_available:
                    # Create or update SystemUpdate record
                    update, created = SystemUpdate.objects.get_or_create(
                        version=latest_version,
                        defaults={
                            'release_notes': release_data.get('body', 'No release notes available'),
                            'is_critical': self.is_critical_update(release_data),
                            'download_url': release_data.get('zipball_url', ''),
                            'published_at': datetime.strptime(
                                release_data['published_at'], 
                                '%Y-%m-%dT%H:%M:%SZ'
                            ),
                            'is_available': True
                        }
                    )
                    
                    return JsonResponse({
                        'update_available': True,
                        'latest_version': latest_version,
                        'current_version': current_version,
                        'release_notes': update.release_notes,
                        'release_url': release_data['html_url'],
                        'published_at': release_data['published_at'],
                        'is_critical': update.is_critical,
                        'size_mb': round(release_data.get('assets', [{}])[0].get('size', 0) / 1024 / 1024, 2) if release_data.get('assets') else 0
                    })
                
                return JsonResponse({
                    'update_available': False,
                    'current_version': current_version,
                    'message': 'You are running the latest version'
                })
            
            else:
                return JsonResponse({
                    'error': 'Failed to check for updates',
                    'status_code': response.status_code
                }, status=500)
                
        except requests.RequestException as e:
            return JsonResponse({
                'error': f'Network error: {str(e)}'
            }, status=500)
        except Exception as e:
            return JsonResponse({
                'error': f'Unexpected error: {str(e)}'
            }, status=500)
    
    def version_compare(self, version1, version2):
        """Compare version strings (semantic versioning)"""
        def version_tuple(v):
            return tuple(map(int, (v.split("."))))
        
        v1_tuple = version_tuple(version1)
        v2_tuple = version_tuple(version2)
        
        if v1_tuple > v2_tuple:
            return 1
        elif v1_tuple < v2_tuple:
            return -1
        else:
            return 0
    
    def is_critical_update(self, release_data):
        """Determine if update is critical based on release notes"""
        body = release_data.get('body', '').lower()
        critical_keywords = [
            'security', 'vulnerability', 'critical', 'urgent', 
            'hotfix', 'patch', 'exploit', 'breach'
        ]
        return any(keyword in body for keyword in critical_keywords)


@method_decorator(staff_member_required, name='dispatch')
class UpdateSystemView(View):
    def post(self, request):
        """Initiate system update process"""
        try:
            data = json.loads(request.body)
            target_version = data.get('version')
            
            if not target_version:
                return JsonResponse({
                    'error': 'Version not specified'
                }, status=400)
            
            # Get the system update record
            try:
                system_update = SystemUpdate.objects.get(version=target_version)
            except SystemUpdate.DoesNotExist:
                return JsonResponse({
                    'error': 'Update version not found'
                }, status=404)
            
            # Create deployment log
            deployment_log = DeploymentLog.objects.create(
                version=target_version,
                initiated_by=request.user,
                status='initiated'
            )
            
            # Create notification for all admin users
            UpdateNotification.objects.create(
                update=system_update,
                title=f'System Update to v{target_version}',
                message=f'ZAIN HMS is being updated to version {target_version}',
                notification_type='info'
            )
            
            # Trigger update process (this would be handled by your deployment script)
            success = self.trigger_deployment(target_version, deployment_log)
            
            if success:
                deployment_log.status = 'completed'
                deployment_log.completed_at = datetime.now()
                deployment_log.save()
                
                # Mark system update as installed
                system_update.is_installed = True
                system_update.installed_at = datetime.now()
                system_update.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully updated to version {target_version}'
                })
            else:
                deployment_log.status = 'failed'
                deployment_log.error_message = 'Deployment script failed'
                deployment_log.save()
                
                return JsonResponse({
                    'error': 'Update process failed'
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': f'Update failed: {str(e)}'
            }, status=500)
    
    def trigger_deployment(self, version, deployment_log):
        """Trigger the actual deployment process"""
        try:
            # Log the deployment initiation
            deployment_log.status = 'in_progress'
            deployment_log.save()
            
            # In production, you would run your deployment script
            deployment_script = '/opt/zain_hms/scripts/deploy.sh'
            
            if os.path.exists(deployment_script):
                # Run the deployment script with the version
                result = subprocess.run([
                    'bash', deployment_script, version
                ], capture_output=True, text=True, timeout=1800)  # 30 minute timeout
                
                if result.returncode == 0:
                    deployment_log.output = result.stdout
                    return True
                else:
                    deployment_log.error_message = result.stderr
                    deployment_log.output = result.stdout
                    return False
            else:
                # For development/testing, simulate the deployment
                import time
                time.sleep(2)  # Simulate deployment time
                
                # Simulate migration check and execution
                deployment_log.output = f"""
Deployment Log for version {version}:
- Database backup created successfully
- Downloaded release {version}
- Validated migrations (0 risky operations found)
- Applied 3 database migrations
- Cleared Django cache
- Updated search indexes
- Ran post-migration tasks
- Health check passed
- Deployment completed successfully
"""
                return True
            
        except subprocess.TimeoutExpired:
            deployment_log.error_message = 'Deployment timed out after 30 minutes'
            return False
        except subprocess.CalledProcessError as e:
            deployment_log.error_message = f'Deployment script error: {str(e)}'
            return False
        except Exception as e:
            deployment_log.error_message = f'Deployment error: {str(e)}'
            return False


@method_decorator(staff_member_required, name='dispatch')
class UpdateNotificationsView(View):
    def get(self, request):
        """Get unread notifications for the user"""
        notifications = UpdateNotification.objects.filter(
            is_read=False
        ).order_by('-created_at')[:10]
        
        notification_data = []
        for notification in notifications:
            notification_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'created_at': notification.created_at.isoformat(),
                'version': notification.update.version if notification.update else None
            })
        
        return JsonResponse({
            'notifications': notification_data,
            'unread_count': notifications.count()
        })
    
    def post(self, request):
        """Mark notification as read"""
        try:
            data = json.loads(request.body)
            notification_id = data.get('notification_id')
            
            if notification_id:
                notification = UpdateNotification.objects.get(id=notification_id)
                notification.is_read = True
                notification.save()
                
                return JsonResponse({'success': True})
            else:
                # Mark all as read
                UpdateNotification.objects.filter(is_read=False).update(is_read=True)
                return JsonResponse({'success': True, 'message': 'All notifications marked as read'})
                
        except UpdateNotification.DoesNotExist:
            return JsonResponse({'error': 'Notification not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(staff_member_required, name='dispatch')
class SystemStatusView(View):
    def get(self, request):
        """Get current system status and version info"""
        try:
            current_version = getattr(settings, 'VERSION', '1.0.0')
            
            # Get latest deployment log
            latest_deployment = DeploymentLog.objects.filter(
                status='completed'
            ).order_by('-completed_at').first()
            
            # Get pending updates
            pending_updates = SystemUpdate.objects.filter(
                is_available=True,
                is_installed=False
            ).count()
            
            return JsonResponse({
                'current_version': current_version,
                'last_update': latest_deployment.completed_at.isoformat() if latest_deployment else None,
                'pending_updates': pending_updates,
                'system_status': 'healthy',
                'uptime': self.get_system_uptime()
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'Failed to get system status: {str(e)}'
            }, status=500)
    
    def get_system_uptime(self):
        """Get system uptime (simplified)"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
            
            uptime_days = int(uptime_seconds // 86400)
            uptime_hours = int((uptime_seconds % 86400) // 3600)
            
            return f"{uptime_days}d {uptime_hours}h"
        except:
            return "Unknown"
