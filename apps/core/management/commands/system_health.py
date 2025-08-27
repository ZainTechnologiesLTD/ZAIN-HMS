# apps/core/management/commands/system_health.py
from django.core.management.base import BaseCommand
from apps.core.health import SystemMonitor
import json


class Command(BaseCommand):
    help = 'Check system health and display metrics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output in JSON format',
        )
        parser.add_argument(
            '--alerts-only',
            action='store_true',
            help='Show only alerts',
        )
    
    def handle(self, *args, **options):
        monitor = SystemMonitor()
        status = monitor.get_system_status()
        
        if options['json']:
            self.stdout.write(json.dumps(status, indent=2))
            return
        
        if options['alerts_only']:
            if status['alerts']:
                self.stdout.write(self.style.WARNING('ALERTS:'))
                for alert in status['alerts']:
                    style = self.style.ERROR if alert['severity'] == 'critical' else self.style.WARNING
                    self.stdout.write(style(f"  {alert['type']}: {alert['message']}"))
            else:
                self.stdout.write(self.style.SUCCESS('No alerts'))
            return
        
        # Display full status
        status_style = {
            'healthy': self.style.SUCCESS,
            'warning': self.style.WARNING,
            'critical': self.style.ERROR
        }
        
        self.stdout.write(f"System Status: {status_style[status['status']](status['status'].upper())}")
        self.stdout.write(f"Last Updated: {status['last_updated']}")
        
        # Display metrics
        metrics = status['metrics']
        self.stdout.write('\nSYSTEM METRICS:')
        self.stdout.write(f"  CPU Usage: {metrics['cpu']['percent']:.1f}%")
        self.stdout.write(f"  Memory Usage: {metrics['memory']['percent']:.1f}% ({metrics['memory']['available_gb']:.1f}GB available)")
        self.stdout.write(f"  Disk Usage: {metrics['disk']['percent']:.1f}% ({metrics['disk']['free_gb']:.1f}GB free)")
        
        if metrics['database']['status'] == 'healthy':
            self.stdout.write(f"  Database Response: {metrics['database']['response_time_ms']:.1f}ms")
        else:
            self.stdout.write(self.style.ERROR(f"  Database: {metrics['database']['status']}"))
        
        # Display alerts
        if status['alerts']:
            self.stdout.write('\nALERTS:')
            for alert in status['alerts']:
                style = self.style.ERROR if alert['severity'] == 'critical' else self.style.WARNING
                self.stdout.write(style(f"  {alert['type']}: {alert['message']}"))
        else:
            self.stdout.write(self.style.SUCCESS('\nNo alerts'))
