# apps/core/backup.py
import os
import shutil
import subprocess
import gzip
import tarfile
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from django.core.files.storage import default_storage
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """Database and media backup management"""
    
    def __init__(self):
        self.backup_dir = getattr(settings, 'DBBACKUP_STORAGE_OPTIONS', {}).get(
            'location', 
            settings.BASE_DIR / 'backups'
        )
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Ensure backup directory exists"""
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for subdir in ['database', 'media', 'logs']:
            Path(self.backup_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    def backup_database(self):
        """Create database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            return self._backup_sqlite(timestamp)
        elif settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
            return self._backup_postgresql(timestamp)
        else:
            raise NotImplementedError("Backup not supported for this database engine")
    
    def _backup_sqlite(self, timestamp):
        """Backup SQLite database"""
        db_path = settings.DATABASES['default']['NAME']
        backup_filename = f"backup_{timestamp}.sqlite3.gz"
        backup_path = Path(self.backup_dir) / 'database' / backup_filename
        
        try:
            # Copy and compress database file
            with open(db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise
    
    def _backup_postgresql(self, timestamp):
        """Backup PostgreSQL database"""
        db_config = settings.DATABASES['default']
        backup_filename = f"backup_{timestamp}.sql.gz"
        backup_path = Path(self.backup_dir) / 'database' / backup_filename
        
        try:
            # Use pg_dump to create backup
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['PASSWORD']
            
            cmd = [
                'pg_dump',
                '-h', db_config['HOST'],
                '-p', str(db_config['PORT']),
                '-U', db_config['USER'],
                '-d', db_config['NAME'],
                '--no-password',
                '--verbose'
            ]
            
            with gzip.open(backup_path, 'wt') as f:
                subprocess.run(cmd, stdout=f, env=env, check=True)
            
            logger.info(f"Database backup created: {backup_path}")
            return backup_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Database backup failed: {e}")
            raise
    
    def backup_media(self):
        """Create media files backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"media_backup_{timestamp}.tar.gz"
        backup_path = Path(self.backup_dir) / 'media' / backup_filename
        
        try:
            media_root = settings.MEDIA_ROOT
            
            with tarfile.open(backup_path, 'w:gz') as tar:
                tar.add(media_root, arcname='media')
            
            logger.info(f"Media backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Media backup failed: {e}")
            raise
    
    def restore_database(self, backup_path):
        """Restore database from backup"""
        if not Path(backup_path).exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            return self._restore_sqlite(backup_path)
        elif settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
            return self._restore_postgresql(backup_path)
        else:
            raise NotImplementedError("Restore not supported for this database engine")
    
    def _restore_sqlite(self, backup_path):
        """Restore SQLite database"""
        db_path = settings.DATABASES['default']['NAME']
        
        try:
            # Close all connections
            connection.close()
            
            # Backup current database
            current_backup = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(db_path, current_backup)
            
            # Restore from backup
            with gzip.open(backup_path, 'rb') as f_in:
                with open(db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            raise
    
    def _restore_postgresql(self, backup_path):
        """Restore PostgreSQL database"""
        db_config = settings.DATABASES['default']
        
        try:
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['PASSWORD']
            
            # Drop and recreate database
            cmd_drop = [
                'dropdb',
                '-h', db_config['HOST'],
                '-p', str(db_config['PORT']),
                '-U', db_config['USER'],
                '--if-exists',
                db_config['NAME']
            ]
            
            cmd_create = [
                'createdb',
                '-h', db_config['HOST'],
                '-p', str(db_config['PORT']),
                '-U', db_config['USER'],
                db_config['NAME']
            ]
            
            cmd_restore = [
                'psql',
                '-h', db_config['HOST'],
                '-p', str(db_config['PORT']),
                '-U', db_config['USER'],
                '-d', db_config['NAME']
            ]
            
            subprocess.run(cmd_drop, env=env, check=False)  # May fail if DB doesn't exist
            subprocess.run(cmd_create, env=env, check=True)
            
            with gzip.open(backup_path, 'rt') as f:
                subprocess.run(cmd_restore, stdin=f, env=env, check=True)
            
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Database restore failed: {e}")
            raise
    
    def cleanup_old_backups(self, keep_days=30):
        """Remove old backup files"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        for backup_type in ['database', 'media']:
            backup_subdir = Path(self.backup_dir) / backup_type
            
            if backup_subdir.exists():
                for backup_file in backup_subdir.iterdir():
                    if backup_file.is_file():
                        file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                        if file_time < cutoff_date:
                            backup_file.unlink()
                            logger.info(f"Removed old backup: {backup_file}")
    
    def list_backups(self):
        """List available backups"""
        backups = {'database': [], 'media': []}
        
        for backup_type in ['database', 'media']:
            backup_subdir = Path(self.backup_dir) / backup_type
            
            if backup_subdir.exists():
                for backup_file in backup_subdir.iterdir():
                    if backup_file.is_file():
                        backups[backup_type].append({
                            'name': backup_file.name,
                            'path': str(backup_file),
                            'size': backup_file.stat().st_size,
                            'created': datetime.fromtimestamp(backup_file.stat().st_mtime)
                        })
        
        return backups
    
    def verify_backup(self, backup_path):
        """Verify backup file integrity"""
        try:
            if backup_path.endswith('.gz'):
                with gzip.open(backup_path, 'rb') as f:
                    f.read(1024)  # Try to read first chunk
            elif backup_path.endswith('.tar.gz'):
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.getnames()  # Verify archive structure
            
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed for {backup_path}: {e}")
            return False
