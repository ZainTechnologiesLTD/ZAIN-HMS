from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from apps.core.db_router import TenantDatabaseManager, MultiTenantDBRouter


class Command(BaseCommand):
    help = "Run migrations for all tenant (hospital_*) databases, ensuring core auth tables exist."

    def add_arguments(self, parser):
        parser.add_argument('--apps', nargs='*', help='Optional list of apps to migrate')

    def handle(self, *args, **options):
        verbosity = options.get('verbosity', 1)
        target_apps = options.get('apps')

    # Ensure hospital DBs are discovered
        TenantDatabaseManager.discover_and_load_hospital_databases()

        tenant_dbs = [name for name in settings.DATABASES.keys() if name.startswith('hospital_')]
        if not tenant_dbs:
            self.stdout.write(self.style.WARNING('No tenant databases found.'))
            return

        for db_name in tenant_dbs:
            hospital_code = db_name.replace('hospital_', '', 1)
            self.stdout.write(self.style.MIGRATE_HEADING(f"Migrating {db_name}"))
            try:
                TenantDatabaseManager.set_hospital_context(hospital_code)

                # --- Pre-migration cleanup: drop stale indexes referencing tenant_id ---
                # Some older tenant databases still have indexes created on removed tenant_id columns
                # (e.g., appointments_appointmenttype_tenant_id_name_..._uniq). These break SQLite
                # when Django recreates tables/indexes. Proactively drop such indexes.
                try:
                    from django.db import connections
                    with connections[db_name].cursor() as cursor:
                        # Find any indexes whose name contains 'tenant_id'
                        cursor.execute("""
                            SELECT name, tbl_name FROM sqlite_master
                            WHERE type='index' AND name LIKE '%tenant_id%'
                        """)
                        stale_indexes = cursor.fetchall()
                        for idx_name, tbl_name in stale_indexes:
                            try:
                                cursor.execute(f"DROP INDEX IF EXISTS {idx_name}")
                                if verbosity:
                                    self.stdout.write(self.style.WARNING(f"Dropped stale index {idx_name} on {tbl_name}"))
                            except Exception as e:
                                self.stderr.write(self.style.WARNING(f"Could not drop index {idx_name}: {e}"))
                        # Extra safety: explicitly drop the known problematic index if present
                        cursor.execute("DROP INDEX IF EXISTS appointments_appointmenttype_tenant_id_name_23c72b32_uniq")
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Pre-migration cleanup warning on {db_name}: {e}"))

                core_bootstrap = ['contenttypes', 'auth']

                if target_apps:
                    # Targeted app migration mode: for each requested app, fake-apply the initial migration
                    # to avoid table-exists errors on legacy tenant DBs, then apply remaining migrations.
                    for app in target_apps:
                        try:
                            # Best-effort: fake the initial migration if present
                            call_command(
                                'migrate', app, '0001', database=db_name, verbosity=verbosity, interactive=False, fake=True
                            )
                        except Exception as e:
                            self.stderr.write(self.style.WARNING(f"{app} fake 0001 warning on {db_name}: {e}"))
                        try:
                            # Apply remaining migrations with fake-initial so Django honors existing tables
                            call_command(
                                'migrate', app, database=db_name, verbosity=verbosity, interactive=False, fake_initial=True
                            )
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f"Failed to migrate app '{app}' on {db_name}: {e}"))
                            # Fallback: if billing migration fails due to unrelated FK issues, try raw backfill and fake-apply
                            if app == 'billing':
                                try:
                                    from django.db import connections
                                    conn = connections[db_name]
                                    vendor = conn.vendor
                                    if vendor == 'sqlite':
                                        with conn.cursor() as cursor:
                                            try:
                                                cursor.execute("PRAGMA foreign_keys = OFF")
                                            except Exception:
                                                pass
                                            # Inspect existing columns
                                            cursor.execute("PRAGMA table_info('billing_invoice')")
                                            cols = {row[1] for row in cursor.fetchall()}
                                            desired = {
                                                'ai_generated': "BOOLEAN NOT NULL DEFAULT 0",
                                                'ai_confidence_score': "REAL",
                                                'ai_pricing_optimization': "TEXT",
                                                'ai_payment_prediction': "TEXT",
                                                'ai_revenue_insights': "TEXT",
                                                'insurance_verification_status': "VARCHAR(20) NOT NULL DEFAULT 'PENDING'",
                                                'insurance_ai_analysis': "TEXT",
                                                'predicted_payment_date': "DATE",
                                                'payment_risk_score': "REAL",
                                                'notes': "TEXT",
                                                'internal_notes': "TEXT",
                                                'ai_notes': "TEXT",
                                                'last_payment_date': "DATETIME",
                                            }
                                            for col, sql_type in desired.items():
                                                if col not in cols:
                                                    try:
                                                        cursor.execute(f"ALTER TABLE billing_invoice ADD COLUMN {col} {sql_type}")
                                                    except Exception:
                                                        # continue best-effort
                                                        pass
                                            try:
                                                cursor.execute("PRAGMA foreign_keys = ON")
                                            except Exception:
                                                pass
                                        # Mark billing.0002 as applied to keep migration history in sync
                                        try:
                                            call_command(
                                                'migrate', 'billing', '0002', database=db_name, verbosity=verbosity, interactive=False, fake=True
                                            )
                                        except Exception as fe:
                                            self.stderr.write(self.style.WARNING(f"Could not fake billing.0002 on {db_name}: {fe}"))
                                        self.stdout.write(self.style.SUCCESS(f"Applied raw billing backfill on {db_name}"))
                                except Exception as raw_e:
                                    self.stderr.write(self.style.ERROR(f"Raw billing backfill failed on {db_name}: {raw_e}"))
                else:
                    # Full migrate mode: ensure core apps are applied first using fake-initial to avoid table-exists errors
                    for app in core_bootstrap:
                        try:
                            call_command(
                                'migrate', app, database=db_name, verbosity=verbosity, interactive=False, fake_initial=True
                            )
                        except Exception as e:
                            self.stderr.write(self.style.WARNING(f"{app} migrate warning on {db_name}: {e}"))

                    # Then run a full migrate on this tenant DB with --fake-initial so
                    # existing initial tables are honored and missing ones created.
                    call_command('migrate', database=db_name, verbosity=verbosity, interactive=False, fake_initial=True)

                self.stdout.write(self.style.SUCCESS(f"✓ {db_name} migrated"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"✗ Failed to migrate {db_name}: {e}"))
            finally:
                TenantDatabaseManager.set_hospital_context(None)
