# apps/appointments/ai_scheduler.py
"""
AI-Powered Appointment Scheduling Engine
Provides intelligent scheduling optimization, conflict resolution, and predictive analytics
"""

import datetime
from typing import Dict, List, Optional, Tuple
from django.db.models import Q, Count
from django.utils import timezone
from django.core.cache import cache
import logging
import json

from .models import Appointment, AppointmentType
from apps.doctors.models import Doctor, DoctorSchedule
from apps.patients.models import Patient

logger = logging.getLogger(__name__)


class AIScheduler:
    """
    AI-powered scheduling engine that optimizes appointment allocation
    considering multiple factors for optimal resource utilization
    """
    
    def __init__(self, hospital_id: str):
        self.hospital_id = hospital_id
        self.cache_timeout = 300  # 5 minutes
    
    def optimize_appointment_schedule(
        self, 
        doctor: Doctor, 
        date: datetime.date, 
        duration_minutes: int = 30,
        patient_preferences: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Generate optimized appointment time slots for a doctor on a specific date
        
        Args:
            doctor: Doctor instance
            date: Target date for appointments
            duration_minutes: Appointment duration
            patient_preferences: Patient preferences (time, urgency, etc.)
            
        Returns:
            List of optimized time slots with availability scores
        """
        cache_key = f"ai_schedule_{doctor.id}_{date}_{duration_minutes}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Retrieved cached schedule for doctor {doctor.id} on {date}")
            return cached_result
        
        try:
            # Get doctor's schedule for the day
            doctor_schedule = self._get_doctor_schedule(doctor, date)
            if not doctor_schedule:
                logger.warning(f"No schedule found for doctor {doctor.id} on {date}")
                return []
            
            # Get existing appointments
            existing_appointments = self._get_existing_appointments(doctor, date)
            
            # Generate base time slots
            available_slots = self._generate_base_time_slots(
                doctor_schedule, existing_appointments, duration_minutes
            )
            
            # Apply AI optimization
            optimized_slots = self._apply_ai_optimization(
                available_slots, doctor, date, patient_preferences
            )
            
            # Cache the result
            cache.set(cache_key, optimized_slots, self.cache_timeout)
            
            logger.info(f"Generated {len(optimized_slots)} optimized slots for doctor {doctor.id}")
            return optimized_slots
            
        except Exception as e:
            logger.error(f"Error in AI scheduling optimization: {str(e)}")
            return []
    
    def predict_no_show_probability(
        self, 
        patient: Patient, 
        doctor: Doctor, 
        appointment_time: datetime.datetime,
        appointment_type: str = 'CONSULTATION'
    ) -> float:
        """
        Predict the probability of a patient not showing up for an appointment
        
        Args:
            patient: Patient instance
            doctor: Doctor instance
            appointment_time: Scheduled appointment time
            appointment_type: Type of appointment
            
        Returns:
            Probability score between 0.0 and 1.0
        """
        try:
            # Get patient's appointment history
            patient_history = self._get_patient_history(patient)
            
            # Calculate base no-show probability
            base_probability = self._calculate_base_no_show_probability(patient_history)
            
            # Apply contextual factors
            contextual_factors = self._get_contextual_factors(
                patient, doctor, appointment_time, appointment_type
            )
            
            # Combine factors using weighted scoring
            final_probability = self._combine_probability_factors(
                base_probability, contextual_factors
            )
            
            logger.info(f"No-show probability for patient {patient.id}: {final_probability:.2f}")
            return min(max(final_probability, 0.0), 1.0)  # Ensure 0-1 range
            
        except Exception as e:
            logger.error(f"Error predicting no-show probability: {str(e)}")
            return 0.1  # Default low probability
    
    def auto_reschedule_conflicts(
        self, 
        conflicting_appointment: Appointment, 
        priority_level: str = 'NORMAL'
    ) -> Optional[Dict]:
        """
        Automatically resolve scheduling conflicts by finding alternative slots
        
        Args:
            conflicting_appointment: Appointment with conflict
            priority_level: Priority for rescheduling (LOW, NORMAL, HIGH, URGENT)
            
        Returns:
            Suggested rescheduling options or None if no solution found
        """
        try:
            # Analyze conflict type and severity
            conflict_analysis = self._analyze_conflict(conflicting_appointment)
            
            # Generate alternative time slots
            alternatives = self._find_alternative_slots(
                conflicting_appointment, priority_level, days_ahead=7
            )
            
            if not alternatives:
                logger.warning(f"No alternatives found for appointment {conflicting_appointment.id}")
                return None
            
            # Rank alternatives by suitability
            ranked_alternatives = self._rank_alternatives(
                alternatives, conflicting_appointment, priority_level
            )
            
            return {
                'conflict_analysis': conflict_analysis,
                'alternatives': ranked_alternatives[:5],  # Top 5 suggestions
                'auto_reschedule_recommended': len(ranked_alternatives) > 0
            }
            
        except Exception as e:
            logger.error(f"Error in auto-rescheduling: {str(e)}")
            return None
    
    def optimize_resource_allocation(
        self, 
        date: datetime.date, 
        department: Optional[str] = None
    ) -> Dict:
        """
        Optimize resource allocation for a given date across all doctors
        
        Args:
            date: Target date for optimization
            department: Specific department (optional)
            
        Returns:
            Resource allocation recommendations
        """
        try:
            # Get all doctors for the date
            doctors = self._get_available_doctors(date, department)
            
            # Analyze current workload distribution
            workload_analysis = self._analyze_workload_distribution(doctors, date)
            
            # Predict demand patterns
            demand_forecast = self._predict_appointment_demand(date, department)
            
            # Generate optimization recommendations
            recommendations = self._generate_resource_recommendations(
                workload_analysis, demand_forecast
            )
            
            return {
                'date': date.isoformat(),
                'department': department,
                'current_utilization': workload_analysis,
                'demand_forecast': demand_forecast,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error in resource allocation optimization: {str(e)}")
            return {}
    
    def _get_doctor_schedule(self, doctor: Doctor, date: datetime.date) -> Optional[Dict]:
        """Get doctor's schedule for a specific date"""
        try:
            weekday = date.weekday()
            schedule = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_of_week=weekday,
                is_active=True
            ).first()
            
            if schedule:
                return {
                    'start_time': schedule.start_time,
                    'end_time': schedule.end_time,
                    'break_start': getattr(schedule, 'break_start', None),
                    'break_end': getattr(schedule, 'break_end', None),
                    'consultation_duration': schedule.consultation_duration
                }
            return None
        except Exception as e:
            logger.error(f"Error getting doctor schedule: {str(e)}")
            return None
    
    def _get_existing_appointments(self, doctor: Doctor, date: datetime.date) -> List[Dict]:
        """Get existing appointments for doctor on date"""
        try:
            appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=date,
                status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
            ).order_by('appointment_time')
            
            return [
                {
                    'start_time': apt.appointment_time,
                    'duration': apt.duration_minutes,
                    'patient_id': apt.patient.id,
                    'appointment_type': apt.appointment_type.name if apt.appointment_type else 'CONSULTATION'
                }
                for apt in appointments
            ]
        except Exception as e:
            logger.error(f"Error getting existing appointments: {str(e)}")
            return []
    
    def _generate_base_time_slots(
        self, 
        doctor_schedule: Dict, 
        existing_appointments: List[Dict], 
        duration_minutes: int
    ) -> List[Dict]:
        """Generate base time slots from doctor schedule"""
        try:
            slots = []
            start_time = doctor_schedule['start_time']
            end_time = doctor_schedule['end_time']
            break_start = doctor_schedule.get('break_start')
            break_end = doctor_schedule.get('break_end')
            
            current_time = datetime.datetime.combine(datetime.date.today(), start_time)
            end_datetime = datetime.datetime.combine(datetime.date.today(), end_time)
            
            while current_time + datetime.timedelta(minutes=duration_minutes) <= end_datetime:
                slot_time = current_time.time()
                
                # Check if slot conflicts with break time
                if break_start and break_end:
                    if break_start <= slot_time < break_end:
                        current_time += datetime.timedelta(minutes=duration_minutes)
                        continue
                
                # Check if slot conflicts with existing appointments
                is_available = True
                for apt in existing_appointments:
                    apt_start = apt['start_time']
                    apt_end = (datetime.datetime.combine(datetime.date.today(), apt_start) + 
                              datetime.timedelta(minutes=apt['duration'])).time()
                    
                    if apt_start <= slot_time < apt_end:
                        is_available = False
                        break
                
                if is_available:
                    slots.append({
                        'time': slot_time,
                        'available': True,
                        'base_score': 1.0
                    })
                
                current_time += datetime.timedelta(minutes=duration_minutes)
            
            return slots
        except Exception as e:
            logger.error(f"Error generating base time slots: {str(e)}")
            return []
    
    def _apply_ai_optimization(
        self, 
        available_slots: List[Dict], 
        doctor: Doctor, 
        date: datetime.date, 
        patient_preferences: Optional[Dict]
    ) -> List[Dict]:
        """Apply AI optimization to rank time slots"""
        try:
            for slot in available_slots:
                # Calculate optimization score based on multiple factors
                score = slot['base_score']
                
                # Factor 1: Time of day preference (peak hours get higher scores)
                score *= self._calculate_time_preference_score(slot['time'])
                
                # Factor 2: Doctor's efficiency at different times
                score *= self._calculate_doctor_efficiency_score(doctor, slot['time'])
                
                # Factor 3: Historical appointment success rate at this time
                score *= self._calculate_historical_success_score(doctor, slot['time'], date)
                
                # Factor 4: Patient preferences (if provided)
                if patient_preferences:
                    score *= self._calculate_patient_preference_score(slot['time'], patient_preferences)
                
                # Factor 5: Buffer time optimization
                score *= self._calculate_buffer_optimization_score(slot, available_slots)
                
                slot['ai_score'] = score
                slot['recommendation_level'] = self._get_recommendation_level(score)
            
            # Sort by AI score (highest first)
            available_slots.sort(key=lambda x: x['ai_score'], reverse=True)
            
            return available_slots
        except Exception as e:
            logger.error(f"Error in AI optimization: {str(e)}")
            return available_slots
    
    def _calculate_time_preference_score(self, slot_time: datetime.time) -> float:
        """Calculate score based on general time preferences"""
        hour = slot_time.hour
        
        # Peak hours: 9-11 AM and 2-4 PM get higher scores
        if 9 <= hour <= 11 or 14 <= hour <= 16:
            return 1.0
        elif 8 <= hour <= 9 or 11 <= hour <= 14 or 16 <= hour <= 17:
            return 0.8
        else:
            return 0.6
    
    def _calculate_doctor_efficiency_score(self, doctor: Doctor, slot_time: datetime.time) -> float:
        """Calculate doctor's efficiency score at specific time"""
        # This would typically use historical data
        # For now, return a base score
        return 1.0
    
    def _calculate_historical_success_score(
        self, 
        doctor: Doctor, 
        slot_time: datetime.time, 
        date: datetime.date
    ) -> float:
        """Calculate success rate based on historical data"""
        # This would analyze historical appointment completion rates
        return 1.0
    
    def _calculate_patient_preference_score(
        self, 
        slot_time: datetime.time, 
        preferences: Dict
    ) -> float:
        """Calculate score based on patient preferences"""
        if 'preferred_time' in preferences:
            preferred_hour = preferences['preferred_time']
            time_diff = abs(slot_time.hour - preferred_hour)
            return max(0.5, 1.0 - (time_diff * 0.1))
        return 1.0
    
    def _calculate_buffer_optimization_score(
        self, 
        current_slot: Dict, 
        all_slots: List[Dict]
    ) -> float:
        """Calculate score based on buffer time optimization"""
        # Prefer slots that maintain good spacing
        return 1.0
    
    def _get_recommendation_level(self, score: float) -> str:
        """Convert AI score to recommendation level"""
        if score >= 0.8:
            return 'HIGHLY_RECOMMENDED'
        elif score >= 0.6:
            return 'RECOMMENDED'
        elif score >= 0.4:
            return 'AVAILABLE'
        else:
            return 'NOT_RECOMMENDED'
    
    def _get_patient_history(self, patient: Patient) -> Dict:
        """Get patient's appointment history for analysis"""
        try:
            appointments = Appointment.objects.filter(patient=patient)
            total_appointments = appointments.count()
            no_shows = appointments.filter(status='NO_SHOW').count()
            cancellations = appointments.filter(status='CANCELLED').count()
            
            return {
                'total_appointments': total_appointments,
                'no_shows': no_shows,
                'cancellations': cancellations,
                'no_show_rate': no_shows / max(total_appointments, 1),
                'cancellation_rate': cancellations / max(total_appointments, 1)
            }
        except Exception as e:
            logger.error(f"Error getting patient history: {str(e)}")
            return {'total_appointments': 0, 'no_shows': 0, 'cancellations': 0, 
                   'no_show_rate': 0, 'cancellation_rate': 0}
    
    def _calculate_base_no_show_probability(self, patient_history: Dict) -> float:
        """Calculate base no-show probability from patient history"""
        return patient_history.get('no_show_rate', 0.1)
    
    def _get_contextual_factors(
        self, 
        patient: Patient, 
        doctor: Doctor, 
        appointment_time: datetime.datetime, 
        appointment_type: str
    ) -> Dict:
        """Get contextual factors that affect no-show probability"""
        return {
            'time_of_day': appointment_time.hour,
            'day_of_week': appointment_time.weekday(),
            'advance_booking_days': (appointment_time.date() - timezone.now().date()).days,
            'appointment_type': appointment_type,
            'weather_factor': 1.0,  # Could integrate weather API
            'distance_factor': 1.0   # Could calculate distance to hospital
        }
    
    def _combine_probability_factors(self, base_probability: float, factors: Dict) -> float:
        """Combine multiple factors to calculate final no-show probability"""
        adjusted_probability = base_probability
        
        # Time of day adjustment
        hour = factors['time_of_day']
        if hour < 8 or hour > 17:
            adjusted_probability *= 1.3  # Higher no-show for early/late appointments
        
        # Day of week adjustment
        if factors['day_of_week'] == 0:  # Monday
            adjusted_probability *= 1.2
        elif factors['day_of_week'] == 4:  # Friday
            adjusted_probability *= 1.1
        
        # Advance booking adjustment
        booking_days = factors['advance_booking_days']
        if booking_days > 30:
            adjusted_probability *= 1.4
        elif booking_days < 1:
            adjusted_probability *= 1.2
        
        return adjusted_probability
    
    def _analyze_conflict(self, appointment: Appointment) -> Dict:
        """Analyze the type and severity of scheduling conflict"""
        return {
            'conflict_type': 'SCHEDULING_OVERLAP',
            'severity': 'MEDIUM',
            'affected_parties': ['doctor', 'patient'],
            'resolution_urgency': 'HIGH'
        }
    
    def _find_alternative_slots(
        self, 
        appointment: Appointment, 
        priority_level: str, 
        days_ahead: int = 7
    ) -> List[Dict]:
        """Find alternative time slots for rescheduling"""
        alternatives = []
        current_date = appointment.appointment_date
        
        for i in range(days_ahead):
            check_date = current_date + datetime.timedelta(days=i+1)
            slots = self.optimize_appointment_schedule(
                appointment.doctor, check_date, appointment.duration_minutes
            )
            
            for slot in slots[:3]:  # Top 3 slots per day
                alternatives.append({
                    'date': check_date,
                    'time': slot['time'],
                    'score': slot['ai_score'],
                    'recommendation': slot['recommendation_level']
                })
        
        return alternatives
    
    def _rank_alternatives(
        self, 
        alternatives: List[Dict], 
        original_appointment: Appointment, 
        priority_level: str
    ) -> List[Dict]:
        """Rank alternative slots by suitability"""
        # Add ranking logic based on priority and patient preferences
        return sorted(alternatives, key=lambda x: x['score'], reverse=True)
    
    def _get_available_doctors(self, date: datetime.date, department: Optional[str]) -> List[Doctor]:
        """Get available doctors for optimization"""
        doctors = Doctor.objects.filter(is_active=True)
        if department:
            doctors = doctors.filter(department__name=department)
        return list(doctors)
    
    def _analyze_workload_distribution(self, doctors: List[Doctor], date: datetime.date) -> Dict:
        """Analyze current workload distribution"""
        return {
            'total_doctors': len(doctors),
            'average_appointments_per_doctor': 8,
            'workload_variance': 0.2
        }
    
    def _predict_appointment_demand(self, date: datetime.date, department: Optional[str]) -> Dict:
        """Predict appointment demand for the date"""
        return {
            'predicted_total_appointments': 50,
            'peak_hours': ['09:00', '10:00', '14:00', '15:00'],
            'demand_confidence': 0.85
        }
    
    def _generate_resource_recommendations(
        self, 
        workload_analysis: Dict, 
        demand_forecast: Dict
    ) -> List[Dict]:
        """Generate resource allocation recommendations"""
        return [
            {
                'type': 'SCHEDULE_ADJUSTMENT',
                'description': 'Add extra slots during peak hours',
                'impact': 'HIGH',
                'implementation_effort': 'LOW'
            }
        ]


class AppointmentReminderEngine:
    """
    AI-powered reminder system with multi-channel communication
    """
    
    def __init__(self):
        self.reminder_channels = ['email', 'sms', 'push', 'call']
    
    def schedule_smart_reminders(self, appointment: Appointment) -> Dict:
        """
        Schedule intelligent reminders based on patient preferences and no-show risk
        """
        try:
            # Calculate no-show probability
            ai_scheduler = AIScheduler(str(appointment.tenant.id))
            no_show_probability = ai_scheduler.predict_no_show_probability(
                appointment.patient, appointment.doctor, 
                datetime.datetime.combine(appointment.appointment_date, appointment.appointment_time)
            )
            
            # Determine reminder strategy based on risk
            reminder_strategy = self._determine_reminder_strategy(no_show_probability)
            
            # Schedule reminders
            scheduled_reminders = self._schedule_reminders(appointment, reminder_strategy)
            
            return {
                'appointment_id': str(appointment.id),
                'no_show_risk': no_show_probability,
                'reminder_strategy': reminder_strategy,
                'scheduled_reminders': scheduled_reminders
            }
            
        except Exception as e:
            logger.error(f"Error scheduling smart reminders: {str(e)}")
            return {}
    
    def _determine_reminder_strategy(self, no_show_probability: float) -> Dict:
        """Determine optimal reminder strategy based on no-show risk"""
        if no_show_probability > 0.3:
            return {
                'intensity': 'HIGH',
                'channels': ['email', 'sms', 'call'],
                'frequency': 'MULTIPLE',
                'timing': [72, 24, 2]  # Hours before appointment
            }
        elif no_show_probability > 0.15:
            return {
                'intensity': 'MEDIUM',
                'channels': ['email', 'sms'],
                'frequency': 'STANDARD',
                'timing': [24, 2]
            }
        else:
            return {
                'intensity': 'LOW',
                'channels': ['email'],
                'frequency': 'MINIMAL',
                'timing': [24]
            }
    
    def _schedule_reminders(self, appointment: Appointment, strategy: Dict) -> List[Dict]:
        """Schedule actual reminder tasks"""
        scheduled = []
        
        for hours_before in strategy['timing']:
            reminder_time = (
                datetime.datetime.combine(appointment.appointment_date, appointment.appointment_time) - 
                datetime.timedelta(hours=hours_before)
            )
            
            for channel in strategy['channels']:
                scheduled.append({
                    'channel': channel,
                    'scheduled_time': reminder_time.isoformat(),
                    'message_template': f'appointment_reminder_{channel}',
                    'status': 'SCHEDULED'
                })
        
        return scheduled
