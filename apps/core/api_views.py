# apps/core/api_views.py
from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import Hospital, Department
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.billing.models import Bill
from apps.emergency.models import EmergencyCase
from .models import Notification, ActivityLog, SystemConfiguration, FileUpload
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
        hospital = getattr(self.request, 'hospital', None)
        if hospital:
            return Notification.objects.filter(
                recipient=self.request.user,
                hospital=hospital
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
        hospital = getattr(request, 'hospital', None)
        if hospital:
            Notification.objects.filter(
                recipient=request.user,
                hospital=hospital,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
        return Response({'status': 'all notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get unread notifications count"""
        hospital = getattr(request, 'hospital', None)
        if hospital:
            count = Notification.objects.filter(
                recipient=request.user,
                hospital=hospital,
                is_read=False
            ).count()
        else:
            count = 0
        return Response({'unread_count': count})


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Activity Log API ViewSet (Read-only)"""
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        hospital = getattr(self.request, 'hospital', None)
        user = self.request.user
        
        # Only admins can view all activity logs
        if user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser:
            if hospital:
                return ActivityLog.objects.filter(hospital=hospital).order_by('-timestamp')
        else:
            # Regular users can only view their own activity logs
            if hospital:
                return ActivityLog.objects.filter(
                    hospital=hospital,
                    user=user
                ).order_by('-timestamp')
        
        return ActivityLog.objects.none()


class DashboardStatsAPIView(APIView):
    """Dashboard statistics API"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        hospital = getattr(request, 'hospital', None)
        if not hospital:
            return Response({'error': 'Hospital not found'}, status=400)
        
        user = request.user
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Base filters
        hospital_filter = {'hospital': hospital}
        today_filter = {**hospital_filter, 'created_at__date': today}
        week_filter = {**hospital_filter, 'created_at__date__gte': week_start}
        month_filter = {**hospital_filter, 'created_at__date__gte': month_start}
        
        stats = {}
        
        if user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser:
            stats = {
                'overview': {
                    'total_patients': Patient.objects.filter(**hospital_filter).count(),
                    'total_doctors': User.objects.filter(**hospital_filter, role='DOCTOR', is_active=True).count(),
                    'total_nurses': User.objects.filter(**hospital_filter, role='NURSE', is_active=True).count(),
                    'total_appointments': Appointment.objects.filter(**hospital_filter).count(),
                },
                'today': {
                    'new_patients': Patient.objects.filter(**today_filter).count(),
                    'appointments': Appointment.objects.filter(
                        hospital=hospital, appointment_date=today
                    ).count(),
                    'emergency_cases': EmergencyCase.objects.filter(**today_filter).count(),
                    'revenue': Bill.objects.filter(**today_filter, status='PAID').aggregate(
                        total=Sum('total_amount')
                    )['total'] or 0,
                },
                'this_week': {
                    'new_patients': Patient.objects.filter(**week_filter).count(),
                    'appointments': Appointment.objects.filter(
                        hospital=hospital, 
                        appointment_date__gte=week_start
                    ).count(),
                    'revenue': Bill.objects.filter(**week_filter, status='PAID').aggregate(
                        total=Sum('total_amount')
                    )['total'] or 0,
                },
                'this_month': {
                    'new_patients': Patient.objects.filter(**month_filter).count(),
                    'appointments': Appointment.objects.filter(
                        hospital=hospital,
                        appointment_date__gte=month_start
                    ).count(),
                    'revenue': Bill.objects.filter(**month_filter, status='PAID').aggregate(
                        total=Sum('total_amount')
                    )['total'] or 0,
                },
                'pending': {
                    'appointments': Appointment.objects.filter(**hospital_filter, status='SCHEDULED').count(),
                    'bills': Bill.objects.filter(**hospital_filter, status='PENDING').count(),
                    'emergency_cases': EmergencyCase.objects.filter(
                        **hospital_filter, status__in=['WAITING', 'IN_PROGRESS']
                    ).count(),
                }
            }
        elif user.role == 'DOCTOR':
            doctor_appointments = Appointment.objects.filter(doctor=user, **hospital_filter)
            stats = {
                'my_stats': {
                    'total_appointments': doctor_appointments.count(),
                    'appointments_today': doctor_appointments.filter(appointment_date=today).count(),
                    'pending_appointments': doctor_appointments.filter(status='SCHEDULED').count(),
                    'completed_appointments': doctor_appointments.filter(status='COMPLETED').count(),
                    'total_patients': doctor_appointments.values('patient').distinct().count(),
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
        
        hospital = getattr(request, 'hospital', None)
        if not hospital:
            return Response({'results': []})
        
        results = []
        
        # Search patients
        patients = Patient.objects.filter(
            Q(hospital=hospital) & (
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
                Q(hospital=hospital, role='DOCTOR') & (
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
                Q(hospital=hospital) & (
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
        hospital = getattr(self.request, 'hospital', None)
        if hospital:
            obj, created = SystemConfiguration.objects.get_or_create(hospital=hospital)
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
        hospital = getattr(request, 'hospital', None)
        if not hospital:
            return Response({'error': 'Hospital not found'}, status=400)
        
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=400)
        
        # Create file upload record
        file_upload = FileUpload.objects.create(
            hospital=hospital,
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
        hospital = getattr(request, 'hospital', None)
        notification_ids = request.data.get('notification_ids', [])
        
        if notification_ids:
            # Mark specific notifications as read
            notifications = Notification.objects.filter(
                id__in=notification_ids,
                recipient=request.user,
                hospital=hospital
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
                hospital=hospital,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
        
        return Response({'updated_count': updated_count})


class BulkNotificationActionAPIView(APIView):
    """Bulk notification actions API"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        hospital = getattr(request, 'hospital', None)
        notification_ids = request.data.get('notification_ids', [])
        action = request.data.get('action', '')
        
        if not notification_ids or not action:
            return Response({'error': 'Invalid request'}, status=400)
        
        notifications = Notification.objects.filter(
            id__in=notification_ids,
            recipient=request.user,
            hospital=hospital
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
            'action': action,
            'updated_count': updated_count
        })
