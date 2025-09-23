# apps/radiology/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import (
    StudyType, RadiologyOrder, RadiologyOrderItem, 
    ImagingStudy, ImagingImage, RadiologyEquipment
)
from apps.patients.models import Patient
from apps.doctors.models import Doctor


class StudyTypeForm(forms.ModelForm):
    class Meta:
        model = StudyType
        fields = [
            'name', 'code', 'description', 'modality', 'price', 
            'estimated_duration_minutes', 'preparation_instructions', 
            'contrast_required', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter study type name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., CT-CHEST'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the imaging study'
            }),
            'modality': forms.Select(attrs={
                'class': 'form-select'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'estimated_duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Duration in minutes'
            }),
            'preparation_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Patient preparation instructions'
            }),
            'contrast_required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['code'].required = True
        self.fields['modality'].required = True
        self.fields['price'].required = True


class RadiologyOrderForm(forms.ModelForm):
    class Meta:
        model = RadiologyOrder
        fields = [
            'patient', 'ordering_doctor', 'clinical_indication', 
            'priority', 'scheduled_date', 'special_instructions'
        ]
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'form-select',
                'id': 'patient-select'
            }),
            'ordering_doctor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'clinical_indication': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Clinical indication for imaging'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'scheduled_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Special instructions'
            }),
        }

    def __init__(self, *args, **kwargs):
        # ZAIN HMS unified system - no hospital filtering needed
        super().__init__(*args, **kwargs)
        
        # Set querysets for all patients and doctors in unified system
        self.fields['patient'].queryset = Patient.objects.all()
        self.fields['ordering_doctor'].queryset = Doctor.objects.all()
        
        self.fields['patient'].required = True
        self.fields['ordering_doctor'].required = True
        self.fields['clinical_indication'].required = True


class RadiologyOrderItemForm(forms.ModelForm):
    class Meta:
        model = RadiologyOrderItem
        fields = ['study_type', 'laterality']
        widgets = {
            'study_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'laterality': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


# Inline formset for order items
RadiologyOrderItemFormSet = inlineformset_factory(
    RadiologyOrder,
    RadiologyOrderItem,
    form=RadiologyOrderItemForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True
)


class ImagingStudyForm(forms.ModelForm):
    class Meta:
        model = ImagingStudy
        fields = [
            'order_item', 'study_date', 'modality', 
            'body_part', 'technique', 'contrast_used', 
            'contrast_agent'
        ]
        widgets = {
            'order_item': forms.Select(attrs={
                'class': 'form-select'
            }),
            'study_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'modality': forms.Select(attrs={
                'class': 'form-select'
            }),
            'body_part': forms.Select(attrs={
                'class': 'form-select'
            }),
            'technique': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Technical notes about the procedure'
            }),
            'contrast_used': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'contrast_agent': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Type of contrast agent'
            }),
        }

    def __init__(self, *args, **kwargs):
        # ZAIN HMS unified system - no hospital filtering needed
        super().__init__(*args, **kwargs)
        
        # Set queryset for all radiology order items in unified system
        self.fields['order_item'].queryset = RadiologyOrderItem.objects.all()


class RadiologistReportForm(forms.ModelForm):
    class Meta:
        model = ImagingStudy
        fields = [
            'findings', 'impression', 'recommendations', 
            'study_quality'
        ]
        widgets = {
            'findings': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Detailed radiological findings'
            }),
            'impression': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Clinical impression based on findings'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recommendations for further care'
            }),
            'study_quality': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['findings'].required = True
        self.fields['impression'].required = True


class RadiologyEquipmentForm(forms.ModelForm):
    class Meta:
        model = RadiologyEquipment
        fields = [
            'name', 'manufacturer', 'model', 'serial_number',
            'equipment_type', 'status', 'room_number', 'location_description',
            'installation_date', 'last_maintenance', 'next_maintenance', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Equipment name'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Manufacturer name'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Model number'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Serial number'
            }),
            'equipment_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'room_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Room number'
            }),
            'location_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Location description'
            }),
            'installation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'last_maintenance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'next_maintenance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['manufacturer'].required = True
        self.fields['model'].required = True


class ImagingImageForm(forms.ModelForm):
    class Meta:
        model = ImagingImage
        fields = ['dicom_file', 'image_file', 'description', 'series_number', 'instance_number']
        widgets = {
            'dicom_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.dcm'
            }),
            'image_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Image description'
            }),
            'series_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'instance_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
        }


# Inline formset for imaging images
ImagingImageFormSet = inlineformset_factory(
    ImagingStudy,
    ImagingImage,
    form=ImagingImageForm,
    extra=1,
    can_delete=True
)
