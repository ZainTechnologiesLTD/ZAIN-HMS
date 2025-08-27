from django.core.management.base import BaseCommand
from django.db import transaction
from apps.laboratory.models import LabSection, TestCategory, LabTest


class Command(BaseCommand):
    help = 'Set up default laboratory sections and test categories'

    def handle(self, *args, **options):
        with transaction.atomic():
            self.create_lab_sections()
            self.stdout.write(
                self.style.SUCCESS('Successfully set up laboratory sections')
            )

    def create_lab_sections(self):
        """Create default laboratory sections and categories"""
        
        # Clinical Biochemistry (Blood Tests)
        biochemistry_section, created = LabSection.objects.get_or_create(
            code='BCH',
            defaults={
                'name': 'Clinical Biochemistry',
                'description': 'Blood chemistry and metabolic tests',
                'requires_digital_signature': True,
                'report_header': 'CLINICAL BIOCHEMISTRY REPORT',
                'report_footer': 'Results are valid only with authorized signature',
            }
        )
        
        if created:
            self.stdout.write(f'Created section: {biochemistry_section.name}')
            
            # Categories for Biochemistry
            categories = [
                ('Liver Function Tests', 'Tests for liver enzyme levels and function'),
                ('Kidney Function Tests', 'Tests for kidney function and electrolytes'),
                ('Lipid Profile', 'Cholesterol and lipid metabolism tests'),
                ('Diabetes Tests', 'Blood glucose and diabetes monitoring'),
                ('Cardiac Markers', 'Heart disease and cardiac function tests'),
                ('Thyroid Function', 'Thyroid hormone levels and function'),
            ]
            
            for cat_name, cat_desc in categories:
                TestCategory.objects.get_or_create(
                    section=biochemistry_section,
                    name=cat_name,
                    defaults={'description': cat_desc}
                )

        # Hematology (Blood Cell Tests)
        hematology_section, created = LabSection.objects.get_or_create(
            code='HEM',
            defaults={
                'name': 'Hematology',
                'description': 'Blood cell counts and related tests',
                'requires_digital_signature': True,
                'report_header': 'HEMATOLOGY REPORT',
            }
        )
        
        if created:
            self.stdout.write(f'Created section: {hematology_section.name}')
            
            categories = [
                ('Complete Blood Count', 'CBC and blood cell analysis'),
                ('Coagulation Studies', 'Blood clotting and bleeding disorders'),
                ('Blood Typing', 'ABO and Rh blood group testing'),
                ('Hemoglobin Studies', 'Hemoglobin variants and disorders'),
            ]
            
            for cat_name, cat_desc in categories:
                TestCategory.objects.get_or_create(
                    section=hematology_section,
                    name=cat_name,
                    defaults={'description': cat_desc}
                )

        # Clinical Microbiology
        microbiology_section, created = LabSection.objects.get_or_create(
            code='MIC',
            defaults={
                'name': 'Clinical Microbiology',
                'description': 'Bacterial, viral, and fungal infection tests',
                'requires_digital_signature': True,
                'report_header': 'MICROBIOLOGY REPORT',
            }
        )
        
        if created:
            self.stdout.write(f'Created section: {microbiology_section.name}')
            
            categories = [
                ('Bacterial Culture', 'Bacterial identification and sensitivity'),
                ('Urine Culture', 'Urinary tract infection testing'),
                ('Blood Culture', 'Bloodstream infection testing'),
                ('Stool Culture', 'Gastrointestinal infection testing'),
                ('Respiratory Culture', 'Respiratory tract infection testing'),
            ]
            
            for cat_name, cat_desc in categories:
                TestCategory.objects.get_or_create(
                    section=microbiology_section,
                    name=cat_name,
                    defaults={'description': cat_desc}
                )

        # Urine Analysis
        urine_section, created = LabSection.objects.get_or_create(
            code='URI',
            defaults={
                'name': 'Urine Analysis',
                'description': 'Urine chemistry and microscopic examination',
                'requires_digital_signature': True,
                'report_header': 'URINE ANALYSIS REPORT',
            }
        )
        
        if created:
            self.stdout.write(f'Created section: {urine_section.name}')
            
            categories = [
                ('Routine Urine', 'Basic urine chemistry and microscopy'),
                ('Urine Protein', 'Protein levels and kidney function'),
                ('Urine Microscopy', 'Cellular elements and crystals'),
                ('Special Urine Tests', 'Specialized urine chemistry tests'),
            ]
            
            for cat_name, cat_desc in categories:
                TestCategory.objects.get_or_create(
                    section=urine_section,
                    name=cat_name,
                    defaults={'description': cat_desc}
                )

        # Immunology & Serology
        immunology_section, created = LabSection.objects.get_or_create(
            code='IMM',
            defaults={
                'name': 'Immunology & Serology',
                'description': 'Immune system and antibody tests',
                'requires_digital_signature': True,
                'report_header': 'IMMUNOLOGY & SEROLOGY REPORT',
            }
        )
        
        if created:
            self.stdout.write(f'Created section: {immunology_section.name}')
            
            categories = [
                ('Infectious Disease Serology', 'Antibody tests for infections'),
                ('Autoimmune Tests', 'Autoimmune disease markers'),
                ('Tumor Markers', 'Cancer screening and monitoring'),
                ('Hormone Tests', 'Endocrine system testing'),
            ]
            
            for cat_name, cat_desc in categories:
                TestCategory.objects.get_or_create(
                    section=immunology_section,
                    name=cat_name,
                    defaults={'description': cat_desc}
                )

        # Histopathology
        histopath_section, created = LabSection.objects.get_or_create(
            code='HIS',
            defaults={
                'name': 'Histopathology',
                'description': 'Tissue examination and biopsy analysis',
                'requires_digital_signature': True,
                'report_header': 'HISTOPATHOLOGY REPORT',
            }
        )
        
        if created:
            self.stdout.write(f'Created section: {histopath_section.name}')
            
            categories = [
                ('Surgical Pathology', 'Tissue biopsies and surgical specimens'),
                ('Cytology', 'Cell examination and Pap smears'),
                ('Fine Needle Aspiration', 'FNA biopsy examination'),
                ('Frozen Section', 'Rapid tissue examination'),
            ]
            
            for cat_name, cat_desc in categories:
                TestCategory.objects.get_or_create(
                    section=histopath_section,
                    name=cat_name,
                    defaults={'description': cat_desc}
                )

        self.create_sample_tests()

    def create_sample_tests(self):
        """Create some sample tests for demonstration"""
        
        # Get sections
        biochemistry = LabSection.objects.get(code='BCH')
        hematology = LabSection.objects.get(code='HEM')
        urine = LabSection.objects.get(code='URI')
        
        # Sample biochemistry tests
        liver_function = TestCategory.objects.get(section=biochemistry, name='Liver Function Tests')
        
        sample_tests = [
            {
                'name': 'Alanine Aminotransferase (ALT)',
                'category': liver_function,
                'sample_type': 'BLOOD',
                'price': 25.00,
                'reference_range_male': '7-40 U/L',
                'reference_range_female': '7-40 U/L',
                'units': 'U/L',
            },
            {
                'name': 'Aspartate Aminotransferase (AST)',
                'category': liver_function,
                'sample_type': 'BLOOD',
                'price': 25.00,
                'reference_range_male': '10-40 U/L',
                'reference_range_female': '10-40 U/L',
                'units': 'U/L',
            },
        ]
        
        # Sample hematology tests
        cbc_category = TestCategory.objects.get(section=hematology, name='Complete Blood Count')
        
        sample_tests.extend([
            {
                'name': 'Complete Blood Count (CBC)',
                'category': cbc_category,
                'sample_type': 'BLOOD',
                'price': 15.00,
                'reference_range_male': 'See individual parameters',
                'reference_range_female': 'See individual parameters',
                'units': 'Various',
            },
            {
                'name': 'Hemoglobin',
                'category': cbc_category,
                'sample_type': 'BLOOD',
                'price': 10.00,
                'reference_range_male': '13.5-17.5 g/dL',
                'reference_range_female': '12.0-16.0 g/dL',
                'units': 'g/dL',
            },
        ])
        
        # Sample urine tests
        routine_urine = TestCategory.objects.get(section=urine, name='Routine Urine')
        
        sample_tests.extend([
            {
                'name': 'Urine Routine & Microscopy',
                'category': routine_urine,
                'sample_type': 'URINE',
                'price': 12.00,
                'reference_range_male': 'See individual parameters',
                'reference_range_female': 'See individual parameters',
                'units': 'Various',
            },
        ])
        
        # Create the tests
        for test_data in sample_tests:
            test, created = LabTest.objects.get_or_create(
                name=test_data['name'],
                category=test_data['category'],
                defaults=test_data
            )
            if created:
                self.stdout.write(f'Created test: {test.name}')
