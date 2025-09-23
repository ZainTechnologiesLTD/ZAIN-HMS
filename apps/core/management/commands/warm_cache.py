from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from apps.core.performance import warm_dashboard_cache, warm_system_cache
from apps.patients.models import Patient
from apps.appointments.models import Appointment
from apps.doctors.models import Doctor
from datetime import datetime, timedelta
import logging

logger = logging.getLogger('zain_hms.management')

class Command(BaseCommand):
    help = 'Warm up application cache for better performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='all',
            choices=['all', 'dashboard', 'system', 'analytics'],
            help='Type of cache to warm up',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output',
        )

    def handle(self, *args, **options):
        cache_type = options['type']
        verbose = options['verbose']
        
        start_time = datetime.now()
        
        if verbose:
            self.stdout.write(
                self.style.SUCCESS(f'🔥 Starting cache warming: {cache_type}')
            )
        
        try:
            if cache_type in ['all', 'dashboard']:
                self._warm_dashboard_cache(verbose)
            
            if cache_type in ['all', 'system']:
                self._warm_system_cache(verbose)
            
            if cache_type in ['all', 'analytics']:
                self._warm_analytics_cache(verbose)
                
            duration = datetime.now() - start_time
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Cache warming completed in {duration.total_seconds():.2f} seconds'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Cache warming failed: {str(e)}')
            )
            logger.error(f"Cache warming failed: {e}")

    def _warm_dashboard_cache(self, verbose):
        """Warm dashboard cache"""
        if verbose:
            self.stdout.write('  📊 Warming dashboard cache...')
        
        # Cache key statistics
        stats = {
            'patients': Patient.objects.count(),
            'appointments': Appointment.objects.count(),
            'doctors': Doctor.objects.count(),
        }
        
        cache.set('zain_hms:dashboard:stats', stats, 3600)
        
        # Cache today's appointments
        today = datetime.now().date()
        today_appointments = Appointment.objects.filter(
            appointment_date=today
        ).select_related('patient', 'doctor').count()
        
        cache.set('zain_hms:dashboard:today_appointments', today_appointments, 1800)
        
        if verbose:
            self.stdout.write('    ✓ Dashboard cache warmed')

    def _warm_system_cache(self, verbose):
        """Warm system cache"""
        if verbose:
            self.stdout.write('  ⚙️  Warming system cache...')
        
        warm_system_cache()
        
        if verbose:
            self.stdout.write('    ✓ System cache warmed')

    def _warm_analytics_cache(self, verbose):
        """Warm analytics cache"""
        if verbose:
            self.stdout.write('  📈 Warming analytics cache...')
        
        # Cache monthly trends
        trends = []
        today = datetime.now().date()
        
        for i in range(6):
            month_start = today.replace(day=1) - timedelta(days=i*30)
            month_end = month_start + timedelta(days=30)
            
            count = Appointment.objects.filter(
                appointment_date__gte=month_start,
                appointment_date__lt=month_end
            ).count()
            
            trends.append({
                'month': month_start.strftime('%B %Y'),
                'appointments': count
            })
        
        cache.set('zain_hms:analytics:trends', trends, 1800)
        
        if verbose:
            self.stdout.write('    ✓ Analytics cache warmed')