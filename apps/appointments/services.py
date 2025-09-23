# appointments/services.py
from datetime import datetime, timedelta
from django.utils import timezone
from typing import List, Dict

class AppointmentSchedulingService:
    DEFAULT_APPOINTMENT_DURATION = 30  # minutes
    MAX_DAYS_AHEAD = 30  # how far ahead to allow bookings
    
    def __init__(self, doctor):
        self.doctor = doctor
    
    def get_available_slots(self, start_date: datetime = None, days: int = 7) -> List[Dict]:
        """Get available appointment slots for the doctor"""
        if not start_date:
            start_date = timezone.now()
            
        end_date = start_date + timedelta(days=days)
        available_slots = []
        
        # Check each day's availability
        current_date = start_date.date()
        while current_date <= end_date.date():
            day_slots = self._get_day_slots(current_date)
            if day_slots:
                available_slots.extend(day_slots)
            current_date += timedelta(days=1)
            
        return available_slots
    
    def _get_day_slots(self, date: datetime.date) -> List[Dict]:
        """Get available slots for a specific day"""
        # Get schedule for this day
        schedule = self.doctor.schedules.filter(
            day_of_week=date.weekday(),
            is_active=True
        ).first()
        
        if not schedule:
            return []
            
        # Get existing appointments
        existing_appointments = self.doctor.appointments.filter(
            date_time__date=date,
            status__in=['SCHEDULED', 'CONFIRMED']
        ).values_list('date_time', flat=True)
        
        # Generate potential slots
        slots = []
        current_time = datetime.combine(date, schedule.start_time)
        end_time = datetime.combine(date, schedule.end_time)
        
        while current_time < end_time:
            slot = timezone.make_aware(current_time)
            
            # Skip if slot is in the past or already booked
            if (slot > timezone.now() and 
                slot not in existing_appointments and
                self._is_valid_slot(slot)):
                
                slots.append({
                    'datetime': slot,
                    'display': slot.strftime('%Y-%m-%d %I:%M %p'),
                    'availability': self._get_slot_availability(slot)
                })
                
            current_time += timedelta(minutes=self.DEFAULT_APPOINTMENT_DURATION)
            
        return slots
    
    def _is_valid_slot(self, slot: datetime) -> bool:
        """Additional validation rules for slots"""
        # Add business rules here, for example:
        # - Check if slot is during break time
        # - Check if doctor has reached daily appointment limit
        # - Check if slot conflicts with doctor's leave/holiday
        return True
    
    def _get_slot_availability(self, slot: datetime) -> str:
        """Get availability status of the slot"""
        # Could return: 'AVAILABLE', 'PEAK_HOURS', 'LIMITED'
        return 'AVAILABLE'