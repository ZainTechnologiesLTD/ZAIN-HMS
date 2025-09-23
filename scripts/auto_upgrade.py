#!/usr/bin/env python3
"""
ZAIN HMS Auto-Upgrade System
Safely manages automated updates for production deployment
"""

import os
import sys
import json
import logging
import subprocess
import shutil
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import git
import django
from django.core.management import execute_from_command_line

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zain_hms.settings')
django.setup()

class AutoUpgradeManager:
    """Manages safe automatic upgrades for ZAIN HMS"""
    
    def __init__(self, project_path: str = None):
        self.project_path = Path(project_path or os.getcwd())
        self.backup_path = self.project_path / 'backups' / 'auto_upgrade'
        self.log_file = self.project_path / 'logs' / 'auto_upgrade.log'
        
        # Setup logging
        self.setup_logging()
        
        # Git repository
        try:
            self.repo = git.Repo(self.project_path)
        except git.InvalidGitRepositoryError:
            self.logger.error("Not a valid Git repository")
            sys.exit(1)
    
    def setup_logging(self):
        """Configure logging for auto-upgrade operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def create_backup(self) -> str:
        """Create full system backup before upgrade"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.backup_path / f'backup_{timestamp}'
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Creating backup in {backup_dir}")
        
        # Backup database
        if (self.project_path / 'db.sqlite3').exists():
            shutil.copy2(
                self.project_path / 'db.sqlite3',
                backup_dir / 'db.sqlite3'
            )
            self.logger.info("Database backed up")
        
        # Backup media files
        media_path = self.project_path / 'media'
        if media_path.exists():
            shutil.copytree(
                media_path,
                backup_dir / 'media',
                dirs_exist_ok=True
            )
            self.logger.info("Media files backed up")
        
        # Backup environment files
        for env_file in ['.env', '.env.production']:
            env_path = self.project_path / env_file
            if env_path.exists():
                shutil.copy2(env_path, backup_dir / env_file)
                self.logger.info(f"{env_file} backed up")
        
        # Backup current commit info
        current_commit = self.repo.head.commit.hexsha
        commit_info = {
            'commit': current_commit,
            'branch': str(self.repo.active_branch),
            'timestamp': timestamp,
            'message': self.repo.head.commit.message.strip()
        }
        
        with open(backup_dir / 'commit_info.json', 'w') as f:
            json.dump(commit_info, f, indent=2)
        
        self.logger.info(f"Backup completed: {backup_dir}")
        return str(backup_dir)
    
    def check_for_updates(self) -> Tuple[bool, List[str]]:
        """Check if updates are available"""
        self.logger.info("Checking for updates...")
        
        # Fetch latest changes
        try:
            self.repo.remotes.origin.fetch()
        except Exception as e:
            self.logger.error(f"Failed to fetch updates: {e}")
            return False, []
        
        # Get commits behind
        commits_behind = list(self.repo.iter_commits(
            f'{self.repo.head.commit.hexsha}..origin/{self.repo.active_branch}'
        ))
        
        if not commits_behind:
            self.logger.info("No updates available")
            return False, []
        
        commit_messages = [commit.message.strip() for commit in commits_behind]
        self.logger.info(f"Found {len(commits_behind)} new commits")
        
        return True, commit_messages
    
    def run_pre_upgrade_checks(self) -> bool:
        """Run safety checks before upgrade"""
        self.logger.info("Running pre-upgrade checks...")
        
        checks_passed = 0
        total_checks = 5
        
        # Check 1: Ensure we're in production environment
        if os.getenv('ENVIRONMENT') != 'production':
            self.logger.warning("Not in production environment")
        else:
            checks_passed += 1
        
        # Check 2: Check disk space (need at least 1GB free)
        stat = shutil.disk_usage(self.project_path)
        free_gb = stat.free / (1024**3)
        if free_gb < 1:
            self.logger.error(f"Insufficient disk space: {free_gb:.2f}GB free")
            return False
        else:
            self.logger.info(f"Disk space OK: {free_gb:.2f}GB free")
            checks_passed += 1
        
        # Check 3: Test database connection
        try:
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            self.logger.info("Database connection OK")
            checks_passed += 1
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False
        
        # Check 4: Check if Redis is running (if configured)
        try:
            import redis
            redis_url = os.getenv('REDIS_CACHE_URL', 'redis://127.0.0.1:6379/1')
            r = redis.from_url(redis_url)
            r.ping()
            self.logger.info("Redis connection OK")
            checks_passed += 1
        except Exception as e:
            self.logger.warning(f"Redis check failed: {e}")
        
        # Check 5: Verify backup directory is writable
        try:
            test_file = self.backup_path / 'test_write'
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text('test')
            test_file.unlink()
            self.logger.info("Backup directory writable")
            checks_passed += 1
        except Exception as e:
            self.logger.error(f"Backup directory not writable: {e}")
            return False
        
        success_rate = checks_passed / total_checks
        self.logger.info(f"Pre-upgrade checks: {checks_passed}/{total_checks} passed ({success_rate:.1%})")
        
        return success_rate >= 0.8  # Require 80% of checks to pass
    
    def apply_update(self) -> bool:
        """Apply the update safely"""
        self.logger.info("Applying update...")
        
        try:
            # Pull latest changes
            self.repo.remotes.origin.pull()
            self.logger.info("Code updated from repository")
            
            # Install/update dependencies
            venv_python = self.project_path / 'venv' / 'bin' / 'python'
            pip_install = subprocess.run([
                str(venv_python), '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], cwd=self.project_path, capture_output=True, text=True)
            
            if pip_install.returncode != 0:
                self.logger.error(f"Dependency installation failed: {pip_install.stderr}")
                return False
            self.logger.info("Dependencies updated")
            
            # Run migrations
            migrate_result = subprocess.run([
                str(venv_python), 'manage.py', 'migrate'
            ], cwd=self.project_path, capture_output=True, text=True)
            
            if migrate_result.returncode != 0:
                self.logger.error(f"Migration failed: {migrate_result.stderr}")
                return False
            self.logger.info("Database migrations applied")
            
            # Collect static files
            collectstatic_result = subprocess.run([
                str(venv_python), 'manage.py', 'collectstatic', '--noinput'
            ], cwd=self.project_path, capture_output=True, text=True)
            
            if collectstatic_result.returncode != 0:
                self.logger.error(f"Static files collection failed: {collectstatic_result.stderr}")
                return False
            self.logger.info("Static files collected")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Update application failed: {e}")
            return False
    
    def run_post_upgrade_tests(self) -> bool:
        """Run tests after upgrade to verify system health"""
        self.logger.info("Running post-upgrade tests...")
        
        tests_passed = 0
        total_tests = 4
        
        # Test 1: Django check
        try:
            venv_python = self.project_path / 'venv' / 'bin' / 'python'
            check_result = subprocess.run([
                str(venv_python), 'manage.py', 'check'
            ], cwd=self.project_path, capture_output=True, text=True)
            
            if check_result.returncode == 0:
                self.logger.info("Django system check passed")
                tests_passed += 1
            else:
                self.logger.error(f"Django system check failed: {check_result.stderr}")
        except Exception as e:
            self.logger.error(f"Django check failed: {e}")
        
        # Test 2: Database query test
        try:
            from django.contrib.auth.models import User
            user_count = User.objects.count()
            self.logger.info(f"Database test passed - {user_count} users")
            tests_passed += 1
        except Exception as e:
            self.logger.error(f"Database test failed: {e}")
        
        # Test 3: Static files test
        static_root = self.project_path / 'staticfiles'
        if static_root.exists() and list(static_root.glob('**/*')):
            self.logger.info("Static files test passed")
            tests_passed += 1
        else:
            self.logger.error("Static files test failed")
        
        # Test 4: Import test
        try:
            import apps.core
            self.logger.info("Application import test passed")
            tests_passed += 1
        except Exception as e:
            self.logger.error(f"Application import test failed: {e}")
        
        success_rate = tests_passed / total_tests
        self.logger.info(f"Post-upgrade tests: {tests_passed}/{total_tests} passed ({success_rate:.1%})")
        
        return success_rate >= 0.75  # Require 75% of tests to pass
    
    def rollback_to_backup(self, backup_dir: str) -> bool:
        """Rollback to previous backup if upgrade fails"""
        self.logger.info(f"Rolling back to backup: {backup_dir}")
        
        backup_path = Path(backup_dir)
        
        try:
            # Restore commit info
            commit_info_file = backup_path / 'commit_info.json'
            if commit_info_file.exists():
                with open(commit_info_file) as f:
                    commit_info = json.load(f)
                
                # Reset to previous commit
                self.repo.git.reset('--hard', commit_info['commit'])
                self.logger.info(f"Reverted to commit: {commit_info['commit']}")
            
            # Restore database
            db_backup = backup_path / 'db.sqlite3'
            if db_backup.exists():
                shutil.copy2(db_backup, self.project_path / 'db.sqlite3')
                self.logger.info("Database restored")
            
            # Restore media files
            media_backup = backup_path / 'media'
            if media_backup.exists():
                media_path = self.project_path / 'media'
                if media_path.exists():
                    shutil.rmtree(media_path)
                shutil.copytree(media_backup, media_path)
                self.logger.info("Media files restored")
            
            # Restore environment files
            for env_file in ['.env', '.env.production']:
                env_backup = backup_path / env_file
                if env_backup.exists():
                    shutil.copy2(env_backup, self.project_path / env_file)
                    self.logger.info(f"{env_file} restored")
            
            self.logger.info("Rollback completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False
    
    def restart_services(self) -> bool:
        """Restart web server and application services"""
        self.logger.info("Restarting services...")
        
        services = ['zain-hms', 'nginx', 'redis-server']
        
        for service in services:
            try:
                result = subprocess.run([
                    'sudo', 'systemctl', 'restart', service
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.logger.info(f"{service} restarted successfully")
                else:
                    self.logger.warning(f"Failed to restart {service}: {result.stderr}")
            except Exception as e:
                self.logger.warning(f"Error restarting {service}: {e}")
        
        return True
    
    def perform_upgrade(self, force: bool = False) -> bool:
        """Main upgrade workflow"""
        self.logger.info("=== Starting Auto-Upgrade Process ===")
        
        # Check for updates
        has_updates, commit_messages = self.check_for_updates()
        if not has_updates and not force:
            self.logger.info("No updates available")
            return True
        
        # Run pre-upgrade checks
        if not self.run_pre_upgrade_checks():
            self.logger.error("Pre-upgrade checks failed - aborting")
            return False
        
        # Create backup
        backup_dir = self.create_backup()
        
        # Apply update
        if not self.apply_update():
            self.logger.error("Update failed - rolling back")
            self.rollback_to_backup(backup_dir)
            return False
        
        # Run post-upgrade tests
        if not self.run_post_upgrade_tests():
            self.logger.error("Post-upgrade tests failed - rolling back")
            self.rollback_to_backup(backup_dir)
            return False
        
        # Restart services
        self.restart_services()
        
        self.logger.info("=== Auto-Upgrade Completed Successfully ===")
        
        # Log upgrade summary
        self.logger.info("Upgrade Summary:")
        for i, message in enumerate(commit_messages[:5], 1):
            self.logger.info(f"  {i}. {message}")
        
        return True


def main():
    """Main entry point for auto-upgrade system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZAIN HMS Auto-Upgrade System')
    parser.add_argument('--force', action='store_true', help='Force upgrade even if no updates')
    parser.add_argument('--check-only', action='store_true', help='Only check for updates')
    parser.add_argument('--project-path', help='Path to ZAIN HMS project')
    
    args = parser.parse_args()
    
    # Initialize upgrade manager
    upgrader = AutoUpgradeManager(args.project_path)
    
    if args.check_only:
        has_updates, messages = upgrader.check_for_updates()
        if has_updates:
            print(f"Updates available ({len(messages)} commits)")
            for msg in messages[:3]:
                print(f"  - {msg}")
        else:
            print("No updates available")
        return
    
    # Perform upgrade
    success = upgrader.perform_upgrade(force=args.force)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()