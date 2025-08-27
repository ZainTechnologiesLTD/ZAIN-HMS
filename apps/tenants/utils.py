# apps/tenants/utils.py
from django.conf import settings
import os
import threading

# Thread-safe lock for ALLOWED_HOSTS modifications
_allowed_hosts_lock = threading.Lock()

class AllowedHostsManager:
    """Utility class to manage ALLOWED_HOSTS for hospital subdomains"""
    
    @staticmethod
    def add_hospital_domain(subdomain):
        """Add hospital subdomain to ALLOWED_HOSTS"""
        with _allowed_hosts_lock:
            hospital_domain = f"{subdomain}.localhost"
            
            if hospital_domain not in settings.ALLOWED_HOSTS:
                settings.ALLOWED_HOSTS.append(hospital_domain)
                print(f"Added {hospital_domain} to ALLOWED_HOSTS")
                
                # Also add production domain pattern if exists
                if hasattr(settings, 'PRODUCTION_DOMAIN'):
                    prod_domain = f"{subdomain}.{settings.PRODUCTION_DOMAIN}"
                    if prod_domain not in settings.ALLOWED_HOSTS:
                        settings.ALLOWED_HOSTS.append(prod_domain)
                        print(f"Added {prod_domain} to ALLOWED_HOSTS")
                
                # Save to environment file for persistence
                AllowedHostsManager._save_to_env_file()
                
    @staticmethod
    def remove_hospital_domain(subdomain):
        """Remove hospital subdomain from ALLOWED_HOSTS"""
        with _allowed_hosts_lock:
            hospital_domain = f"{subdomain}.localhost"
            
            if hospital_domain in settings.ALLOWED_HOSTS:
                settings.ALLOWED_HOSTS.remove(hospital_domain)
                print(f"Removed {hospital_domain} from ALLOWED_HOSTS")
                
                # Also remove production domain if exists
                if hasattr(settings, 'PRODUCTION_DOMAIN'):
                    prod_domain = f"{subdomain}.{settings.PRODUCTION_DOMAIN}"
                    if prod_domain in settings.ALLOWED_HOSTS:
                        settings.ALLOWED_HOSTS.remove(prod_domain)
                        print(f"Removed {prod_domain} from ALLOWED_HOSTS")
                
                # Save to environment file for persistence
                AllowedHostsManager._save_to_env_file()
                
    @staticmethod
    def load_hospital_domains():
        """Load all hospital domains from database to ALLOWED_HOSTS at startup"""
        try:
            from .models import Tenant
            
            with _allowed_hosts_lock:
                for hospital in Tenant.objects.all():
                    hospital_domain = f"{hospital.subdomain}.localhost"
                    
                    if hospital_domain not in settings.ALLOWED_HOSTS:
                        settings.ALLOWED_HOSTS.append(hospital_domain)
                        
                    # Also add production domain if exists
                    if hasattr(settings, 'PRODUCTION_DOMAIN'):
                        prod_domain = f"{hospital.subdomain}.{settings.PRODUCTION_DOMAIN}"
                        if prod_domain not in settings.ALLOWED_HOSTS:
                            settings.ALLOWED_HOSTS.append(prod_domain)
                            
                print(f"Loaded {Tenant.objects.count()} hospital domains to ALLOWED_HOSTS")
                
        except Exception as e:
            print(f"Could not load hospital domains: {e}")
            
    @staticmethod
    def _save_to_env_file():
        """Save current ALLOWED_HOSTS to .env file for persistence"""
        try:
            env_file_path = settings.BASE_DIR / '.env'
            
            if env_file_path.exists():
                # Read existing .env content
                with open(env_file_path, 'r') as f:
                    lines = f.readlines()
                
                # Update ALLOWED_HOSTS line
                updated_lines = []
                allowed_hosts_line_found = False
                
                for line in lines:
                    if line.startswith('ALLOWED_HOSTS='):
                        # Update the ALLOWED_HOSTS line
                        hosts_str = ','.join(settings.ALLOWED_HOSTS)
                        updated_lines.append(f'ALLOWED_HOSTS={hosts_str}\n')
                        allowed_hosts_line_found = True
                    else:
                        updated_lines.append(line)
                
                # If ALLOWED_HOSTS line doesn't exist, add it
                if not allowed_hosts_line_found:
                    hosts_str = ','.join(settings.ALLOWED_HOSTS)
                    updated_lines.append(f'ALLOWED_HOSTS={hosts_str}\n')
                
                # Write back to .env file
                with open(env_file_path, 'w') as f:
                    f.writelines(updated_lines)
                    
                print("Updated ALLOWED_HOSTS in .env file")
                
        except Exception as e:
            print(f"Could not save ALLOWED_HOSTS to .env file: {e}")
            
    @staticmethod 
    def get_hospital_url(subdomain):
        """Get the appropriate URL for a hospital based on environment"""
        if settings.DEBUG:
            return f"http://{subdomain}.localhost:8000/"
        else:
            # Production URL
            domain = getattr(settings, 'PRODUCTION_DOMAIN', 'yourdomain.com')
            return f"https://{subdomain}.{domain}/"
