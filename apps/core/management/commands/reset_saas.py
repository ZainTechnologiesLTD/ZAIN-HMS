# apps/core/management/commands/reset_saas.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import connections
import os
import shutil
import time


class Command(BaseCommand):
    help = "Reset the SaaS databases (default and all tenant hospital DBs) with optional backups, then rebuild."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Do not prompt for confirmation")
        parser.add_argument("--no-backup", action="store_true", help="Do not create backups before deletion")
        parser.add_argument("--demo", action="store_true", help="Create a demo hospital after reset")
        parser.add_argument("--superadmin-username", type=str, default="superadmin")
        parser.add_argument("--superadmin-email", type=str, default="admin@zainhms.com")
        parser.add_argument("--superadmin-password", type=str, default="Admin12345")

    def handle(self, *args, **options):
        force = options["force"]
        do_backup = not options["no_backup"]

        if not force:
            answer = input("This will DELETE the default DB and ALL hospital DBs. Continue? [y/N]: ").strip().lower()
            if answer not in ("y", "yes"):
                self.stdout.write(self.style.WARNING("Aborted."))
                return

        # Close database connections
        connections.close_all()

        ts = time.strftime("%Y%m%d-%H%M%S")
        base_dir = settings.BASE_DIR

        # 1) Reset default DB
        default_db_path = settings.DATABASES["default"]["NAME"] if settings.DATABASES["default"]["ENGINE"].endswith("sqlite3") else None
        if default_db_path and os.path.exists(default_db_path):
            if do_backup:
                backup_path = f"{default_db_path}.{ts}.bak"
                shutil.copy2(default_db_path, backup_path)
                self.stdout.write(self.style.SUCCESS(f"Backed up default DB -> {backup_path}"))
            os.remove(default_db_path)
            self.stdout.write(self.style.SUCCESS("Deleted default SQLite DB"))

        # 2) Reset hospitals directory (tenant DBs)
        hospitals_dir = base_dir / "hospitals"
        if hospitals_dir.exists():
            if do_backup:
                backup_dir = base_dir / f"hospitals_backup_{ts}"
                shutil.move(str(hospitals_dir), str(backup_dir))
                self.stdout.write(self.style.SUCCESS(f"Backed up hospitals dir -> {backup_dir}"))
            else:
                shutil.rmtree(hospitals_dir)
                self.stdout.write(self.style.SUCCESS("Deleted hospitals directory"))

        # Ensure fresh hospitals dir exists for future DBs
        os.makedirs(base_dir / "hospitals", exist_ok=True)

        # 3) Re-run migrations for default DB
        self.stdout.write("Running migrate for default DB...")
        call_command("migrate", verbosity=1, interactive=False)
        call_command("createcachetable", verbosity=0)
        self.stdout.write(self.style.SUCCESS("Default DB migrated"))

        # 4) Ensure superadmin exists
        self.stdout.write("Ensuring superadmin exists...")
        try:
            call_command(
                "create_superadmin",
                username=options["superadmin_username"],
                email=options["superadmin_email"],
                password=options["superadmin_password"],
                first_name="Super",
                last_name="Admin",
            )
        except Exception as e:
            # If it already exists, that's fine
            self.stdout.write(self.style.WARNING(f"Superadmin creation skipped: {e}"))

        # 5) Optionally create demo hospital
        if options["demo"]:
            self.stdout.write("Creating demo hospital...")
            try:
                call_command(
                    "setup_hospital",
                    name="Demo General Hospital",
                    code="DEMO001",
                    email="admin@demo-hospital.com",
                    phone="+1-555-0123",
                    address="123 Healthcare Avenue",
                    city="Demo City",
                    state="Demo State",
                    country="USA",
                    postal_code="12345",
                    plan="TRIAL",
                    admin_username="demo_admin",
                    admin_email="admin@demo-hospital.com",
                    admin_password="DemoPass123",
                    admin_first_name="Demo",
                    admin_last_name="Admin",
                )
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Demo hospital creation encountered an issue: {e}"))

        self.stdout.write(self.style.SUCCESS("SaaS reset completed."))
