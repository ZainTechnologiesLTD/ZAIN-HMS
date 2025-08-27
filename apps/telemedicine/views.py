from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .models import TeleconsultationAppointment, VirtualWaitingRoom


@login_required
def telemedicine_dashboard(request):
    """Telemedicine dashboard"""
    context = {
        'title': 'Telemedicine Dashboard',
        'page_name': 'Telemedicine',
    }
    return render(request, 'telemedicine/dashboard.html', context)


@login_required
def teleconsultation_list(request):
    """List of teleconsultation appointments"""
    appointments = TeleconsultationAppointment.objects.all().select_related('patient', 'doctor')
    
    context = {
        'appointments': appointments,
        'title': 'Teleconsultations',
        'page_name': 'Teleconsultations',
    }
    return render(request, 'telemedicine/teleconsultation_list.html', context)


@login_required
def virtual_consultation_room(request, appointment_id):
    """Virtual consultation room"""
    appointment = get_object_or_404(TeleconsultationAppointment, id=appointment_id)
    
    context = {
        'appointment': appointment,
        'title': f'Virtual Consultation - {appointment.patient.user.get_full_name()}',
        'page_name': 'Virtual Consultation',
    }
    return render(request, 'telemedicine/virtual_room.html', context)


@login_required 
def join_consultation(request, appointment_id):
    """Join a consultation"""
    appointment = get_object_or_404(TeleconsultationAppointment, id=appointment_id)
    
    # Update join status based on user role
    waiting_room, created = VirtualWaitingRoom.objects.get_or_create(appointment=appointment)
    
    if request.user.role == 'DOCTOR':
        waiting_room.doctor_joined = True
        waiting_room.doctor_join_time = timezone.now()
    else:
        waiting_room.patient_joined = True 
        waiting_room.patient_join_time = timezone.now()
    
    waiting_room.save()
    
    return JsonResponse({
        'success': True,
        'meeting_url': appointment.meeting_url,
        'room_id': appointment.meeting_room_id
    })
