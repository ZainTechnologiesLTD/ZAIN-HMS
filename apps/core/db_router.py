# apps/core/db_router.py
"""
Multi-tenant database router for SaaS Hospital Management System
Each hospital gets its own database for complete data isolation
"""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import threading
import threading

# Thread-local storage for current hospital context
_thread_local = threading.local()


class MultiTenantDBRouter:
    """
    A router to control all database operations for multi-tenant application
    Each hospital has its own database for complete data isolation
    """
    
    # Apps that should always use the default database
    SHARED_APPS = [
        'admin',
        'auth',
        'contenttypes',
        'sessions',
        'messages',
        'staticfiles',
        'accounts',  # User management and Hospital models
        'core',      # Shared core functionality
        'reports',   # Store reports in shared DB to avoid tenant drift issues
        'radiology', # Temporarily force radiology to use default DB to avoid connection issues
        'pharmacy',  # Temporarily moved to fix missing tables issue
    ]
    
    # Apps that should use tenant-specific databases
    TENANT_APPS = [
        'patients',
        'appointments',
        'doctors',
        'nurses',
        'staff',
        'billing',
        # 'pharmacy',  # Temporarily moved to SHARED_APPS to fix missing tables
        'laboratory',
        # 'radiology',  # Temporarily moved to SHARED_APPS to avoid connection issues
        'emergency',
        'inventory',
        'analytics',
        'hr',
        'surgery',
        'telemedicine',
        'room_management',
        'opd',
        'ipd',
        'notifications',
        'contact',
        'feedback',
        'dashboard',
        'django_celery_beat',
        'django_celery_results',
    ]
    
    def db_for_read(self, model, **hints):
        """Suggest the database to read from"""
        return self._get_database_for_model(model)
    
    def db_for_write(self, model, **hints):
        """Suggest the database to write to"""
        return self._get_database_for_model(model)
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if models are in the same database or are allowed cross-DB relations"""
        # Get model information
        obj1_app = obj1._meta.app_label
        obj1_model = obj1._meta.model_name
        obj2_app = obj2._meta.app_label
        obj2_model = obj2._meta.model_name
        
        # Allow relationships between shared models (they're all in default DB)
        shared_apps = self.SHARED_APPS
        if obj1_app in shared_apps and obj2_app in shared_apps:
            return True
        
        # Allow relationships between tenant models (they're in same hospital DB)
        if obj1_app in self.TENANT_APPS and obj2_app in self.TENANT_APPS:
            return True
        
        # Allow specific cross-database relationships that we know are valid
        # E.g., Doctor (tenant) -> User (shared) relationships
        allowed_cross_db_relations = [
            # (tenant_app, tenant_model, shared_app, shared_model)
            ('doctors', 'doctor', 'accounts', 'user'),
            ('nurses', 'nurse', 'accounts', 'user'),
            ('staff', 'staffprofile', 'accounts', 'user'),
            ('patients', 'patient', 'accounts', 'hospital'),
            ('appointments', 'appointment', 'accounts', 'hospital'),
            ('billing', 'invoice', 'accounts', 'hospital'),
            ('pharmacy', 'pharmacysale', 'accounts', 'hospital'),
            ('reports', 'report', 'accounts', 'hospital'),
            ('reports', 'report', 'accounts', 'user'),
            ('reports', 'reporttemplate', 'accounts', 'hospital'),
            ('reports', 'reporttemplate', 'accounts', 'user'),
        ]
        
        for tenant_app, tenant_model, shared_app, shared_model in allowed_cross_db_relations:
            if ((obj1_app == tenant_app and obj1_model == tenant_model and 
                 obj2_app == shared_app and obj2_model == shared_model) or
                (obj1_app == shared_app and obj1_model == shared_model and 
                 obj2_app == tenant_app and obj2_model == tenant_model)):
                return True
        
        # For other cases, use the default database set logic
        db_set = {'default'}
        hospital_db = self._get_current_hospital_db()
        if hospital_db:
            db_set.add(hospital_db)
            
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
            
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that certain apps' models get created on the right database"""
        
        # Shared apps usually live in default DB
        if app_label in self.SHARED_APPS:
            # Allow auth/contenttypes to migrate on tenant DBs so Django's
            # post_migrate permissions/contenttypes creation doesn't crash.
            if db != 'default' and app_label in ['auth', 'contenttypes']:
                return True
            return db == 'default'
            
        # Tenant apps should migrate to tenant databases
        if app_label in self.TENANT_APPS:
            # Allow migration to default for initial setup
            if db == 'default':
                return False
            # Allow migration to hospital-specific databases
            return db.startswith('hospital_')
            
        # For other apps, allow migration to default
        return db == 'default'
    
    def _get_database_for_model(self, model):
        """Determine which database to use for a given model"""
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        
        # Force certain models to always use default database
        shared_models = [
            ('accounts', 'user'),
            ('accounts', 'hospital'),
            ('accounts', 'usersession'),
            ('auth', 'user'),
            ('auth', 'group'),
            ('auth', 'permission'),
            ('contenttypes', 'contenttype'),
            ('sessions', 'session'),
            ('admin', 'logentry'),
        ]
        
        for app, model_check in shared_models:
            if app_label == app and model_name == model_check:
                return 'default'
        
        # Shared apps always use default database
        if app_label in self.SHARED_APPS:
            return 'default'
            
        # Tenant apps use hospital-specific database
        if app_label in self.TENANT_APPS:
            hospital_db = self._get_current_hospital_db()
            if hospital_db:
                # Validate that the database connection exists and has the required tables
                from django.db import connections
                if hospital_db in connections.databases:
                    try:
                        # Use Django introspection for cross-backend compatibility
                        table_name = model._meta.db_table
                        existing_tables = set(connections[hospital_db].introspection.table_names())
                        if table_name in existing_tables:
                            return hospital_db
                        else:
                            # Prefer hospital DB even if table missing (surface a clear error)
                            return hospital_db
                    except Exception:
                        # On any error, still prefer the hospital DB so issues are visible there
                        return hospital_db
                else:
                    # Database connection doesn't exist, fall back to default
                    return 'default'
            # Fallback to default if no hospital context
            return 'default'
            
        # Default fallback
        return 'default'
    
    def _get_current_hospital_db(self):
        """Get the current hospital's database name from thread-local storage"""
        hospital_db = getattr(_thread_local, 'hospital_db', None)
        
        # Validate that the database connection actually exists
        if hospital_db:
            from django.db import connections
            if hospital_db not in connections.databases:
                # Log the issue for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Database connection '{hospital_db}' does not exist. Available: {list(connections.databases.keys())}")
                return None
                
        return hospital_db


class TenantDatabaseManager:
    """Utility class to manage tenant databases"""
    
    @staticmethod
    def set_hospital_context(hospital_code):
        """Set the current hospital context for database routing"""
        if hospital_code:
            _thread_local.hospital_db = f"hospital_{hospital_code}"
        else:
            _thread_local.hospital_db = None
    
    @staticmethod
    def get_current_hospital_context():
        """Get the current hospital context"""
        return getattr(_thread_local, 'hospital_db', None)
    
    @staticmethod
    def temporarily_use_default_db():
        """Context manager to temporarily use default database for queries"""
        class DefaultDBContext:
            def __init__(self):
                self.original_context = getattr(_thread_local, 'hospital_db', None)
            
            def __enter__(self):
                _thread_local.hospital_db = None
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                _thread_local.hospital_db = self.original_context
        
        return DefaultDBContext()
    
    @staticmethod
    def get_hospital_db_name(hospital_code):
        """Get database name for a hospital"""
        return f"hospital_{hospital_code}"
    
    @staticmethod
    def discover_hospital_databases():
        """
        Discover existing hospital database files and return their codes
        """
        from django.conf import settings
        from pathlib import Path
        import os
        
        hospital_codes = []
        
        # Method 1: Look in the main directory for hospital_*.db files
        base_dir = Path(settings.BASE_DIR)
        for db_file in base_dir.glob('hospital_*.db'):
            # Extract hospital code from filename
            filename = db_file.stem  # removes .db extension
            if filename.startswith('hospital_'):
                code = filename.replace('hospital_', '')
                hospital_codes.append(code)
        
        # Method 2: Look in hospitals subdirectory (if it exists)
        hospitals_dir = base_dir / 'hospitals'
        if hospitals_dir.exists():
            for hospital_dir in hospitals_dir.iterdir():
                if hospital_dir.is_dir():
                    db_file = hospital_dir / 'db.sqlite3'
                    if db_file.exists():
                        hospital_codes.append(hospital_dir.name)
        
        # Remove duplicates and return sorted list
        return sorted(list(set(hospital_codes)))
    
    @staticmethod
    def discover_and_load_hospital_databases():
        """
        Discover existing hospital database files and add them to Django settings
        This should be called at Django startup
        """
        from django.conf import settings
        from pathlib import Path
        import os
        
        hospitals_dir = settings.BASE_DIR / 'hospitals'
        if not hospitals_dir.exists():
            return
        
        # Look for hospital directories with database files
        for hospital_dir in hospitals_dir.iterdir():
            if hospital_dir.is_dir():
                db_file = hospital_dir / 'db.sqlite3'
                if db_file.exists():
                    hospital_code = hospital_dir.name
                    db_name = f"hospital_{hospital_code}"
                    
                    # Add database configuration if not already present
                    if db_name not in settings.DATABASES:
                        db_config = {
                            'ENGINE': 'django.db.backends.sqlite3',
                            'NAME': str(db_file),
                            'OPTIONS': {'timeout': 20},
                            'ATOMIC_REQUESTS': False,
                            'AUTOCOMMIT': True,
                            'CONN_MAX_AGE': 0,
                            'CONN_HEALTH_CHECKS': False,
                            'TIME_ZONE': None,
                            'USER': '',
                            'PASSWORD': '',
                            'HOST': '',
                            'PORT': '',
                            'TEST': {
                                'CHARSET': None,
                                'COLLATION': None,
                                'MIGRATE': True,
                                'MIRROR': None,
                                'NAME': None
                            }
                        }
                        settings.DATABASES[db_name] = db_config
                        print(f"Loaded hospital database: {db_name}")
    
    @staticmethod
    def create_hospital_database(hospital_code, db_config=None):
        """Create a new database for a hospital"""
        from django.core.management import call_command
        from django.conf import settings
        from django.db import connections
        import os
        
        db_name = TenantDatabaseManager.get_hospital_db_name(hospital_code)
        
        # Default database configuration
        if not db_config:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
                # SQLite configuration
                db_config = {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': settings.BASE_DIR / f'hospitals/{hospital_code}/db.sqlite3',
                    'OPTIONS': {'timeout': 20},
                    'ATOMIC_REQUESTS': False,
                    'AUTOCOMMIT': True,
                    'CONN_MAX_AGE': 0,
                    'CONN_HEALTH_CHECKS': False,
                    'TIME_ZONE': None,
                    'USER': '',
                    'PASSWORD': '',
                    'HOST': '',
                    'PORT': '',
                    'TEST': {
                        'CHARSET': None,
                        'COLLATION': None,
                        'MIGRATE': True,
                        'MIRROR': None,
                        'NAME': None
                    }
                }
                # Ensure directory exists
                os.makedirs(settings.BASE_DIR / f'hospitals/{hospital_code}', exist_ok=True)
            else:
                # PostgreSQL configuration (for production)
                db_config = {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': f'zain_hms_{hospital_code}',
                    'USER': settings.DATABASES['default']['USER'],
                    'PASSWORD': settings.DATABASES['default']['PASSWORD'],
                    'HOST': settings.DATABASES['default']['HOST'],
                    'PORT': settings.DATABASES['default']['PORT'],
                    'OPTIONS': settings.DATABASES['default'].get('OPTIONS', {})
                }
        
        # Add database configuration to settings dynamically
        settings.DATABASES[db_name] = db_config
        
        # Force Django to recognize the new database
        connections.close_all()
        if hasattr(connections, '_connections'):
            connections._connections = threading.local()
        
        # Reset the databases dict in connections
        if hasattr(connections, '_databases'):
            connections._databases = None
        
        # Run migrations for the new database
        try:
            # Set hospital context for migration
            TenantDatabaseManager.set_hospital_context(hospital_code)
            
            print(f"Running migrations for {db_name}...")
            
            # First migrate core Django apps
            core_apps = ['contenttypes', 'auth']
            for app in core_apps:
                try:
                    call_command('migrate', app, database=db_name, verbosity=1)
                    print(f"✓ Migrated {app}")
                except Exception as e:
                    print(f"Warning: Failed to migrate {app} to {db_name}: {e}")
            
            # Special-case: pharmacy 0003 creates tables that also exist from
            # 0001/0002 in SQLite and can throw a duplicate table warning.
            # Strategy: migrate pharmacy up to 0002 normally, drop legacy
            # tables if present, then migrate to head.
            try:
                from django.db import connections
                call_command('migrate', 'pharmacy', '0002', database=db_name, verbosity=1)
                # Drop legacy tables if they exist to avoid duplicate-table errors
                with connections[db_name].cursor() as cursor:
                    cursor.execute("DROP TABLE IF EXISTS pharmacy_pharmacysaleitem;")
                    cursor.execute("DROP TABLE IF EXISTS pharmacy_pharmacysale;")
                call_command('migrate', 'pharmacy', database=db_name, verbosity=1)
                print("✓ Migrated pharmacy (handled legacy tables)")
            except Exception as e:
                print(f"Warning: Pharmacy migration workaround failed on {db_name}: {e}")

            # Run migrations for tenant apps only (skip pharmacy, already handled)
            for app in MultiTenantDBRouter.TENANT_APPS:
                if app == 'pharmacy':
                    continue
                try:
                    call_command('migrate', app, database=db_name, verbosity=1)
                    print(f"✓ Migrated {app}")
                except Exception as e:
                    print(f"Warning: Failed to migrate {app} to {db_name}: {e}")
                    
        except Exception as e:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured(f"Failed to create hospital database {db_name}: {e}")
        finally:
            # Clear hospital context
            TenantDatabaseManager.set_hospital_context(None)
    
    @staticmethod
    def delete_hospital_database(hospital_code):
        """Delete a hospital's database (use with extreme caution)"""
        from django.conf import settings
        from django.db import connections
        import os
        
        db_name = TenantDatabaseManager.get_hospital_db_name(hospital_code)
        
        if db_name in settings.DATABASES:
            db_config = settings.DATABASES[db_name]
            
            if db_config['ENGINE'] == 'django.db.backends.sqlite3':
                # Delete SQLite file
                db_path = db_config['NAME']
                if os.path.exists(db_path):
                    os.remove(db_path)
                # Remove directory if empty
                try:
                    os.rmdir(os.path.dirname(db_path))
                except OSError:
                    pass  # Directory not empty
            else:
                # For PostgreSQL, you'd need to connect as superuser and DROP DATABASE
                # This should be handled carefully in production
                pass
            
            # Remove from settings
            del settings.DATABASES[db_name]
            
            # Reset connections
            if db_name in connections.databases:
                del connections.databases[db_name]


# Middleware to set hospital context
class HospitalContextMiddleware:
    """Middleware to set hospital context for database routing"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Clear any existing context
        TenantDatabaseManager.set_hospital_context(None)
        
        # Set hospital context if user is authenticated and has hospital
        if (hasattr(request, 'user') and 
            request.user.is_authenticated):
            
            try:
                # Priority 1: session-selected hospital (for SUPERADMINs / superusers)
                sel_code = request.session.get('selected_hospital_code')
                if sel_code:
                    TenantDatabaseManager.set_hospital_context(sel_code)
                    # Also set request.hospital for convenience in views/templates
                    try:
                        from apps.accounts.models import Hospital
                        with TenantDatabaseManager.temporarily_use_default_db():
                            request.hospital = Hospital.objects.using('default').filter(code=sel_code).first()
                    except Exception:
                        pass
                else:
                    # Priority 2: user's assigned hospital
                    user_hospital_code = None
                    user_hospital = None
                    if hasattr(request.user, 'hospital_id') and request.user.hospital_id:
                        try:
                            # Import apps.accounts.models dynamically to avoid hard dependency on Hospital class
                            from apps.accounts import models as accounts_models
                            Hospital = getattr(accounts_models, 'Hospital', None)
                            if Hospital is not None:
                                with TenantDatabaseManager.temporarily_use_default_db():
                                    hospital = Hospital.objects.using('default').filter(id=request.user.hospital_id).first()
                                    if hospital:
                                        user_hospital_code = hospital.code
                                        user_hospital = hospital
                        except Exception:
                            pass
                    if user_hospital_code:
                        TenantDatabaseManager.set_hospital_context(user_hospital_code)
                        # Set hospital on request for views that need it
                        request.hospital = user_hospital
                    else:
                        # Priority 3 (admin fallback): if hitting admin and user is superuser/SUPERADMIN
                        # and no hospital is selected, pick a sensible default to avoid default DB queries
                        if request.path.startswith('/admin/') and (
                            getattr(request.user, 'is_superuser', False) or getattr(request.user, 'role', '') == 'SUPERADMIN'
                        ):
                            try:
                                from apps.accounts.models import Hospital
                                with TenantDatabaseManager.temporarily_use_default_db():
                                    # Choose session-selected hospital id if present, else first available
                                    h = None
                                    sel_id = request.session.get('selected_hospital_id')
                                    if sel_id:
                                        h = Hospital.objects.using('default').filter(id=sel_id).first()
                                    if not h:
                                        h = Hospital.objects.using('default').order_by('created_at' if hasattr(Hospital, 'created_at') else 'name').first()
                                    if h:
                                        TenantDatabaseManager.set_hospital_context(h.code)
                                        request.hospital = h
                                        # Persist for consistency across requests
                                        request.session['selected_hospital_id'] = str(h.id)
                                        request.session['selected_hospital_name'] = h.name
                                        request.session['selected_hospital_code'] = h.code
                            except Exception:
                                # If anything goes wrong, proceed without forcing a context
                                pass
                # If still no hospital context was set, only auto-select in dev when explicitly enabled
                try:
                    from django.conf import settings as dj_settings
                    auto_select_enabled = getattr(dj_settings, 'AUTO_SELECT_HOSPITAL_IN_DEV', False)
                    if auto_select_enabled and getattr(dj_settings, 'DEBUG', False):
                        if not TenantDatabaseManager.get_current_hospital_context():
                            # Prefer DEMO001 if present, else first discovered hospital code
                            import os
                            hospitals_dir = getattr(dj_settings, 'BASE_DIR', None) / 'hospitals' if hasattr(dj_settings, 'BASE_DIR') else None
                            chosen_code = None
                            if hospitals_dir and os.path.isdir(hospitals_dir):
                                preferred = 'DEMO001'
                                # Use preferred if exists
                                if os.path.isdir(os.path.join(hospitals_dir, preferred)):
                                    chosen_code = preferred
                                else:
                                    # Pick first directory name
                                    for name in os.listdir(hospitals_dir):
                                        if os.path.isdir(os.path.join(hospitals_dir, name)):
                                            chosen_code = name
                                            break
                            if chosen_code:
                                TenantDatabaseManager.set_hospital_context(chosen_code)
                                # Minimal request context to avoid attribute errors in templates/views
                                request.session.setdefault('selected_hospital_code', chosen_code)
                                request.hospital_info = {
                                    'code': chosen_code,
                                    'name': chosen_code,
                                    'logo': None,
                                    'settings': {},
                                }
                except Exception:
                    # Best-effort fallback; ignore any error here
                    pass
            except Exception as e:
                # If there's any error, continue without setting context
                pass
        
        response = self.get_response(request)
        
        # Clear context after request
        TenantDatabaseManager.set_hospital_context(None)
        
        return response
