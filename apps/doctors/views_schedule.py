# apps/doctors/views_schedule.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.forms import modelformset_factory
from django.db.models import Q, Count
from django.utils import timezone
from django.db import transaction
from apps.accounts.models import CustomUser

# Import enhanced models
try:
    from .models import Doctor, DoctorSchedule, DoctorLeave, ScheduleTemplate, ScheduleTemplateSlot
except ImportError:
    # Fallback for backward compatibility
    from .models import Doctor, DoctorSchedule


class DoctorScheduleListView(LoginRequiredMixin, ListView):
    """List all doctor schedules with enhanced filtering and search"""
    model = Doctor
    template_name = 'doctors/schedule_list.html'
    context_object_name = 'doctors'
    paginate_by = 12

    def get_queryset(self):
        # Get current user's hospital context (if any)
        # For ZAIN HMS unified system, use default database
        
        # Base queryset with active doctors only
        queryset = Doctor.objects.filter(is_active=True)
        
        # Search functionality
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            search_filters = Q(first_name__icontains=search_query) | Q(last_name__icontains=search_query)
            
            # Add specialization and license number search if fields exist
            if hasattr(Doctor, 'specialization'):
                search_filters |= Q(specialization__icontains=search_query)
            if hasattr(Doctor, 'license_number'):
                search_filters |= Q(license_number__icontains=search_query)
                
            queryset = queryset.filter(search_filters)
        
        # Department/Specialization filtering
        department = self.request.GET.get('department', '').strip()
        if department and hasattr(Doctor, 'specialization'):
            queryset = queryset.filter(specialization=department)
        
        # Schedule status filtering
        schedule_filter = self.request.GET.get('schedule_status', '')
        if schedule_filter == 'with_schedule':
            queryset = queryset.filter(schedules__isnull=False).distinct()
        elif schedule_filter == 'no_schedule':
            queryset = queryset.filter(schedules__isnull=True)
        
        # Annotate with schedule count
        queryset = queryset.annotate(schedule_count=Count('schedules', distinct=True))
        
        return queryset.order_by('last_name', 'first_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # For ZAIN HMS unified system, use default database
        
        # Get all doctors for stats
        all_doctors = Doctor.objects.filter(is_active=True)
        scheduled_doctors = all_doctors.filter(schedules__isnull=False).distinct()
        
        # Stats data
        context.update({
            'total_doctors': all_doctors.count(),
            'scheduled_doctors': scheduled_doctors.count(),
            'unscheduled_doctors': all_doctors.count() - scheduled_doctors.count(),
        })
        
        # Department choices for filtering
        departments = getattr(Doctor, 'SPECIALIZATION_CHOICES', [])
        context['departments'] = departments
        
        # Current filter values
        context.update({
            'current_search': self.request.GET.get('search', ''),
            'current_department': self.request.GET.get('department', ''),
            'current_schedule_status': self.request.GET.get('schedule_status', ''),
        })
        
        # Recent schedules for display
        recent_schedules = DoctorSchedule.objects.select_related('doctor').order_by('-id')[:10]
        context['recent_schedules'] = recent_schedules
        
        return context


class DoctorScheduleManageView(LoginRequiredMixin, ListView):
    """Enhanced manage schedules for a specific doctor with advanced features"""
    model = DoctorSchedule
    template_name = 'doctors/schedule_manage.html'
    context_object_name = 'schedules'

    def get_queryset(self):
        doctor_id = self.kwargs.get('doctor_id')
        # For ZAIN HMS unified system, use default database
        
        return DoctorSchedule.objects.filter(doctor_id=doctor_id).order_by('day_of_week', 'start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor_id = self.kwargs.get('doctor_id')
        
        # For ZAIN HMS unified system, use default database
        
        doctor = get_object_or_404(Doctor, id=doctor_id)
        context['doctor'] = doctor
        
        # Prepare enhanced schedule data for the template
        schedule_data = {}
        days_of_week = [
            ('Monday', 0), ('Tuesday', 1), ('Wednesday', 2), ('Thursday', 3),
            ('Friday', 4), ('Saturday', 5), ('Sunday', 6)
        ]
        
        # Initialize all days
        for day_name, day_num in days_of_week:
            schedule_data[day_num] = {
                'name': day_name,
                'schedules': [],
                'has_schedules': False
            }
        
        # Group existing schedules by day
        schedules = DoctorSchedule.objects.filter(doctor_id=doctor_id).order_by('day_of_week', 'start_time')
        for schedule in schedules:
            day_num = schedule.day_of_week
            if day_num in schedule_data:
                schedule_data[day_num]['schedules'].append(schedule)
                schedule_data[day_num]['has_schedules'] = True
        
        context['schedule_data'] = schedule_data
        context['days_of_week'] = days_of_week
        
        # Add schedule templates (if they exist and table exists)
        context['schedule_templates'] = []
        try:
            from .models import ScheduleTemplate
            # For ZAIN HMS unified system, use default database
            
            # Try to query schedule templates
            # Get all templates, not just default ones
            context['schedule_templates'] = list(ScheduleTemplate.objects.all()[:10])
        except (ImportError, AttributeError):
            # Handle cases where ScheduleTemplate model doesn't exist
            context['schedule_templates'] = []
        except Exception as e:
            # Handle database errors (table doesn't exist, column missing, etc.)
            import logging
            logging.warning(f"ScheduleTemplate query failed: {e}")
            context['schedule_templates'] = []

        # Provide list of other active doctors for covering doctor selection (limit for performance)
        try:
            context['other_doctors'] = Doctor.objects.filter(is_active=True).exclude(id=doctor.id).order_by('last_name', 'first_name')[:100]
        except Exception:
            context['other_doctors'] = []
            
        return context

    def post(self, request, *args, **kwargs):
        """Handle enhanced schedule updates with break times and patient capacity"""
        doctor_id = self.kwargs.get('doctor_id')
        
        # For ZAIN HMS unified system, use default database
        
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        try:
            # Check if schedule_data is provided (from enhanced form)
            schedule_data = request.POST.get('schedule_data')
            if schedule_data:
                import json
                schedule_dict = json.loads(schedule_data)
                
                with transaction.atomic():
                    # Delete existing schedules for this doctor
                    DoctorSchedule.objects.filter(doctor=doctor).delete()
                    
                    # Create new schedules from JSON data with enhanced features
                    for day_value, slots in schedule_dict.items():
                        for slot in slots:
                            # Create schedule with enhanced fields
                            schedule_obj_data = {
                                'doctor': doctor,
                                'day_of_week': int(day_value),
                                'start_time': slot['start_time'],
                                'end_time': slot['end_time'],
                            }
                            
                            # Add enhanced fields if available
                            if 'break_start_time' in slot and slot['break_start_time']:
                                schedule_obj_data['break_start_time'] = slot['break_start_time']
                            if 'break_end_time' in slot and slot['break_end_time']:
                                schedule_obj_data['break_end_time'] = slot['break_end_time']
                            if 'max_patients' in slot and slot['max_patients']:
                                schedule_obj_data['max_patients'] = int(slot['max_patients'])
                                
                            schedule = DoctorSchedule(**schedule_obj_data)
                            schedule.save()
                
                # Check if it's an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Enhanced schedule updated successfully!'
                    })
                else:
                    messages.success(request, 'Enhanced schedule updated successfully!')
                    return redirect('doctors:schedule_manage', doctor_id=doctor.id)
                    
            else:
                # Handle traditional form submission with enhanced features
                with transaction.atomic():
                    # Delete existing schedules for this doctor
                    DoctorSchedule.objects.filter(doctor=doctor).delete()
                    
                    # Create new schedules from form data
                    for day in range(7):  # 0-6 for Monday-Sunday
                        start_times = request.POST.getlist(f'start_time_{day}')
                        end_times = request.POST.getlist(f'end_time_{day}')
                        break_start_times = request.POST.getlist(f'break_start_time_{day}')
                        break_end_times = request.POST.getlist(f'break_end_time_{day}')
                        max_patients_list = request.POST.getlist(f'max_patients_{day}')
                        
                        for i, (start_time, end_time) in enumerate(zip(start_times, end_times)):
                            if start_time and end_time:
                                schedule_obj_data = {
                                    'doctor': doctor,
                                    'day_of_week': day,
                                    'start_time': start_time,
                                    'end_time': end_time,
                                }
                                
                                # Add enhanced fields if available
                                if i < len(break_start_times) and break_start_times[i]:
                                    schedule_obj_data['break_start_time'] = break_start_times[i]
                                if i < len(break_end_times) and break_end_times[i]:
                                    schedule_obj_data['break_end_time'] = break_end_times[i]
                                if i < len(max_patients_list) and max_patients_list[i]:
                                    schedule_obj_data['max_patients'] = int(max_patients_list[i])
                                    
                                schedule = DoctorSchedule(**schedule_obj_data)
                                schedule.save()
                    
                    # Check if it's an AJAX request
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': 'Enhanced schedule updated successfully!'
                        })
                    else:
                        messages.success(request, 'Enhanced schedule updated successfully!')
                        return redirect('doctors:schedule_manage', doctor_id=doctor.id)
                    
        except Exception as e:
            # Check if it's an AJAX request for error handling too
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Error updating schedule: {str(e)}'
                })
            else:
                messages.error(request, f'Error updating schedule: {str(e)}')
                return self.get(request, *args, **kwargs)


@login_required
def doctor_schedule_api(request, doctor_id):
    """API endpoint to get doctor schedule"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    schedules = DoctorSchedule.objects.filter(doctor=doctor).order_by('day_of_week', 'start_time')
    
    schedule_data = {}
    for schedule in schedules:
        day = schedule.day_of_week
        if day not in schedule_data:
            schedule_data[day] = []
        
        schedule_data[day].append({
            'id': schedule.id,
            'start_time': schedule.start_time.strftime('%H:%M'),
            'end_time': schedule.end_time.strftime('%H:%M'),
        })
    
    return JsonResponse({
        'doctor': {
            'id': doctor.id,
            'name': f"Dr. {doctor.first_name} {doctor.last_name}",
            'specialization': doctor.specialization,
        },
        'schedules': schedule_data
    })


@login_required
def submit_leave_request(request):
    """Handle doctor leave request submissions"""
    if request.method == 'POST':
        try:
            from .models import DoctorLeave
            
            doctor_id = request.POST.get('doctor_id')
            doctor = get_object_or_404(Doctor, id=doctor_id)
            
            # Create leave request
            leave = DoctorLeave.objects.create(
                doctor=doctor,
                leave_type=request.POST.get('leave_type'),
                start_date=request.POST.get('start_date'),
                end_date=request.POST.get('end_date'),
                reason=request.POST.get('reason'),
                contact_info=request.POST.get('contact_info', ''),
                covering_doctor_id=request.POST.get('covering_doctor') or None,
                status='PENDING'
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': 'Leave request submitted successfully and is pending approval.'
                })
            else:
                messages.success(request, 'Leave request submitted successfully!')
                return redirect('doctors:schedule_manage', doctor_id=doctor.id)
                
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)})
            else:
                messages.error(request, f'Error submitting leave request: {str(e)}')
                return redirect('doctors:schedule_manage', doctor_id=doctor_id)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def schedule_template_detail(request, template_id):
    """Return JSON structure of a schedule template."""
    # For ZAIN HMS unified system, use default database

    try:
        from .models import ScheduleTemplate, ScheduleTemplateSlot
    except Exception:
        return JsonResponse({'success': False, 'message': 'Schedule templates not available'}, status=400)

    try:
        template = ScheduleTemplate.objects.get(id=template_id)
    except ScheduleTemplate.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Template not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error retrieving template: {e}'}, status=500)

    # Build schedule data grouped by day
    schedule_data = {}
    try:
        slots = ScheduleTemplateSlot.objects.filter(template=template).order_by('day_of_week', 'start_time')
        for slot in slots:
            day = slot.day_of_week
            if day not in schedule_data:
                schedule_data[day] = {'slots': []}
            schedule_data[day]['slots'].append({
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'break_start_time': slot.break_start_time.strftime('%H:%M') if slot.break_start_time else None,
                'break_end_time': slot.break_end_time.strftime('%H:%M') if slot.break_end_time else None,
                'max_patients': slot.max_patients,
            })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error building template slots: {e}'}, status=500)

    return JsonResponse({
        'success': True,
        'template_name': template.name,
        'schedule_data': schedule_data,
    })


class DoctorScheduleCreateView(LoginRequiredMixin, CreateView):
    """Create a new doctor schedule entry"""
    model = DoctorSchedule
    fields = ['doctor', 'day_of_week', 'start_time', 'end_time']
    template_name = 'doctors/schedule_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Schedule entry created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('doctors:schedule_manage', kwargs={'doctor_id': self.object.doctor.id})


class DoctorScheduleUpdateView(LoginRequiredMixin, UpdateView):
    """Update a doctor schedule entry"""
    model = DoctorSchedule
    fields = ['day_of_week', 'start_time', 'end_time']
    template_name = 'doctors/schedule_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Schedule entry updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('doctors:schedule_manage', kwargs={'doctor_id': self.object.doctor.id})


class DoctorScheduleDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a doctor schedule entry"""
    model = DoctorSchedule
    template_name = 'doctors/schedule_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        doctor_id = self.get_object().doctor.id
        messages.success(request, 'Schedule entry deleted successfully!')
        result = super().delete(request, *args, **kwargs)
        return result

    def get_success_url(self):
        return reverse_lazy('doctors:schedule_manage', kwargs={'doctor_id': self.object.doctor.id})
