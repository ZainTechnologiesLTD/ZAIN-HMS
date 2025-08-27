"""
Management command to create sample radiology study types
Usage: python manage.py create_sample_study_types
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.radiology.models import StudyType
from apps.accounts.models import Hospital, User
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create sample radiology study types for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hospital-id',
            type=str,
            help='Create study types for specific hospital (UUID)',
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing study types before creating new ones',
        )

    def handle(self, *args, **options):
        hospital_id = options.get('hospital_id')
        clear_existing = options.get('clear_existing')
        
        # Get hospitals
        if hospital_id:
            try:
                hospitals = [Hospital.objects.get(id=hospital_id)]
                self.stdout.write(f'Creating study types for hospital: {hospitals[0].name}')
            except Hospital.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Hospital with ID "{hospital_id}" not found')
                )
                return
        else:
            hospitals = Hospital.objects.all()
            if not hospitals.exists():
                self.stdout.write(
                    self.style.ERROR('No hospitals found. Please create a hospital first.')
                )
                return
            self.stdout.write(f'Creating study types for {hospitals.count()} hospital(s)')

        # Get admin user for created_by field
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.filter(role='ADMIN').first()
        
        # Sample study types data
        study_types_data = [
            # X-Ray Studies
            {
                'name': 'Chest X-Ray PA',
                'modality': 'X_RAY',
                'body_part': 'CHEST',
                'description': 'Posterior-anterior chest X-ray for lung and heart evaluation',
                'price': Decimal('75.00'),
                'estimated_duration_minutes': 15,
                'preparation_instructions': 'Remove all metal objects from chest area',
                'contrast_required': False,
                'fasting_required': False,
            },
            {
                'name': 'Chest X-Ray Lateral',
                'modality': 'X_RAY',
                'body_part': 'CHEST',
                'description': 'Lateral chest X-ray for detailed lung evaluation',
                'price': Decimal('85.00'),
                'estimated_duration_minutes': 15,
                'preparation_instructions': 'Remove all metal objects from chest area',
                'contrast_required': False,
                'fasting_required': False,
            },
            {
                'name': 'Abdomen X-Ray',
                'modality': 'X_RAY',
                'body_part': 'ABDOMEN',
                'description': 'Plain abdominal X-ray for bowel and organ evaluation',
                'price': Decimal('80.00'),
                'estimated_duration_minutes': 20,
                'preparation_instructions': 'No specific preparation required',
                'contrast_required': False,
                'fasting_required': False,
            },
            {
                'name': 'Knee X-Ray',
                'modality': 'X_RAY',
                'body_part': 'LOWER_LIMB',
                'description': 'X-ray of knee joint (AP and lateral views)',
                'price': Decimal('90.00'),
                'estimated_duration_minutes': 20,
                'preparation_instructions': 'Remove all metal objects from leg area',
                'contrast_required': False,
                'fasting_required': False,
            },
            {
                'name': 'Spine Lumbar X-Ray',
                'modality': 'X_RAY',
                'body_part': 'SPINE',
                'description': 'Lumbar spine X-ray (AP and lateral views)',
                'price': Decimal('120.00'),
                'estimated_duration_minutes': 25,
                'preparation_instructions': 'Remove all metal objects from lower back area',
                'contrast_required': False,
                'fasting_required': False,
            },
            
            # CT Scans
            {
                'name': 'CT Head Without Contrast',
                'modality': 'CT',
                'body_part': 'HEAD',
                'description': 'CT scan of head without contrast for brain evaluation',
                'price': Decimal('350.00'),
                'estimated_duration_minutes': 30,
                'preparation_instructions': 'Remove all metal objects from head and neck area',
                'contrast_required': False,
                'fasting_required': False,
            },
            {
                'name': 'CT Head With Contrast',
                'modality': 'CT',
                'body_part': 'HEAD',
                'description': 'CT scan of head with IV contrast for detailed brain evaluation',
                'price': Decimal('450.00'),
                'estimated_duration_minutes': 45,
                'preparation_instructions': 'Fast for 4 hours before exam. Remove all metal objects.',
                'contrast_required': True,
                'fasting_required': True,
            },
            {
                'name': 'CT Chest',
                'modality': 'CT',
                'body_part': 'CHEST',
                'description': 'CT scan of chest for lung and mediastinal evaluation',
                'price': Decimal('400.00'),
                'estimated_duration_minutes': 35,
                'preparation_instructions': 'Remove all metal objects from chest area',
                'contrast_required': False,
                'fasting_required': False,
            },
            {
                'name': 'CT Abdomen & Pelvis',
                'modality': 'CT',
                'body_part': 'ABDOMEN',
                'description': 'CT scan of abdomen and pelvis with oral and IV contrast',
                'price': Decimal('550.00'),
                'estimated_duration_minutes': 60,
                'preparation_instructions': 'Fast for 6 hours. Drink oral contrast 1 hour before exam.',
                'contrast_required': True,
                'fasting_required': True,
            },
            
            # MRI Studies
            {
                'name': 'MRI Brain',
                'modality': 'MRI',
                'body_part': 'HEAD',
                'description': 'MRI of brain for detailed neurological evaluation',
                'price': Decimal('750.00'),
                'estimated_duration_minutes': 60,
                'preparation_instructions': 'Remove all metal objects. Inform if you have implants or claustrophobia.',
                'contrast_required': False,
                'fasting_required': False,
            },
            {
                'name': 'MRI Knee',
                'modality': 'MRI',
                'body_part': 'LOWER_LIMB',
                'description': 'MRI of knee for detailed joint and soft tissue evaluation',
                'price': Decimal('650.00'),
                'estimated_duration_minutes': 45,
                'preparation_instructions': 'Remove all metal objects from leg area. Inform if you have implants.',
                'contrast_required': False,
                'fasting_required': False,
            },
            {
                'name': 'MRI Lumbar Spine',
                'modality': 'MRI',
                'body_part': 'SPINE',
                'description': 'MRI of lumbar spine for disc and nerve evaluation',
                'price': Decimal('700.00'),
                'estimated_duration_minutes': 50,
                'preparation_instructions': 'Remove all metal objects. Inform if you have back implants.',
                'contrast_required': False,
                'fasting_required': False,
            },
            
            # Ultrasound Studies
            {
                'name': 'Abdominal Ultrasound',
                'modality': 'ULTRASOUND',
                'body_part': 'ABDOMEN',
                'description': 'Ultrasound of abdominal organs (liver, gallbladder, kidneys)',
                'price': Decimal('180.00'),
                'estimated_duration_minutes': 30,
                'preparation_instructions': 'Fast for 8 hours before exam. Drink water 1 hour before.',
                'contrast_required': False,
                'fasting_required': True,
            },
            {
                'name': 'Pelvic Ultrasound',
                'modality': 'ULTRASOUND',
                'body_part': 'PELVIS',
                'description': 'Ultrasound of pelvic organs (uterus, ovaries, bladder)',
                'price': Decimal('160.00'),
                'estimated_duration_minutes': 25,
                'preparation_instructions': 'Drink 32 oz of water 1 hour before exam. Do not urinate.',
                'contrast_required': False,
                'fasting_required': False,
            },
            {
                'name': 'Thyroid Ultrasound',
                'modality': 'ULTRASOUND',
                'body_part': 'NECK',
                'description': 'Ultrasound of thyroid gland',
                'price': Decimal('140.00'),
                'estimated_duration_minutes': 20,
                'preparation_instructions': 'No preparation required',
                'contrast_required': False,
                'fasting_required': False,
            },
            
            # Mammography
            {
                'name': 'Mammography Screening',
                'modality': 'MAMMOGRAPHY',
                'body_part': 'CHEST',
                'description': 'Screening mammography for breast cancer detection',
                'price': Decimal('220.00'),
                'estimated_duration_minutes': 20,
                'preparation_instructions': 'Do not use deodorant, powder, or lotion on chest area.',
                'contrast_required': False,
                'fasting_required': False,
            },
            {
                'name': 'Mammography Diagnostic',
                'modality': 'MAMMOGRAPHY',
                'body_part': 'CHEST',
                'description': 'Diagnostic mammography for breast abnormality evaluation',
                'price': Decimal('280.00'),
                'estimated_duration_minutes': 30,
                'preparation_instructions': 'Do not use deodorant, powder, or lotion on chest area.',
                'contrast_required': False,
                'fasting_required': False,
            },
        ]

        created_count = 0
        
        for hospital in hospitals:
            self.stdout.write(f'\nProcessing hospital: {hospital.name}')
            
            # Clear existing if requested
            if clear_existing:
                deleted_count = StudyType.objects.filter(hospital=hospital).count()
                StudyType.objects.filter(hospital=hospital).delete()
                self.stdout.write(f'  Deleted {deleted_count} existing study types')
            
            with transaction.atomic():
                for study_data in study_types_data:
                    # Check if study type already exists
                    existing = StudyType.objects.filter(
                        hospital=hospital,
                        name=study_data['name']
                    ).exists()
                    
                    if not existing:
                        study_type = StudyType.objects.create(
                            hospital=hospital,
                            created_by=admin_user,
                            **study_data
                        )
                        created_count += 1
                        self.stdout.write(f'  ✓ Created: {study_type.name} ({study_type.code})')
                    else:
                        self.stdout.write(f'  - Skipped: {study_data["name"]} (already exists)')

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} study types!')
        )
        
        if created_count > 0:
            self.stdout.write('')
            self.stdout.write('Study types have been created with the following modalities:')
            self.stdout.write('• X-Ray: Basic radiographic imaging')
            self.stdout.write('• CT: Computed tomography scans')
            self.stdout.write('• MRI: Magnetic resonance imaging')
            self.stdout.write('• Ultrasound: Ultrasonic imaging')
            self.stdout.write('• Mammography: Breast imaging')
            self.stdout.write('')
            self.stdout.write('You can now create radiology orders with these study types!')
