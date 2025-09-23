# apps/core/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification, ActivityLog, SystemConfiguration, FileUpload
import json
from datetime import datetime, date
from django.contrib.sessions.serializers import JSONSerializer

User = get_user_model()


class DateTimeAwareJSONEncoder(json.JSONEncoder):
    """JSON encoder that can handle datetime objects"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


class DateTimeAwareJSONSerializer(JSONSerializer):
    """Session serializer that can handle datetime objects"""
    def dumps(self, obj):
        return json.dumps(obj, separators=(',', ':'), cls=DateTimeAwareJSONEncoder).encode('latin-1')
    
    def loads(self, data):
        return json.loads(data.decode('latin-1'))


class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    time_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'priority', 'title', 'message', 'data', 'link',
            'is_read', 'read_at', 'created_at', 'sender_name', 'time_since_created'
        ]
        read_only_fields = ['id', 'created_at', 'sender_name', 'time_since_created']
    
    def get_time_since_created(self, obj):
        """Get human-readable time since creation"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return obj.created_at.strftime('%Y-%m-%d')


class ActivityLogSerializer(serializers.ModelSerializer):
    """Activity log serializer"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)
    formatted_timestamp = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'action', 'model_name', 'object_id', 'object_repr',
            'ip_address', 'timestamp', 'user_name', 'user_role',
            'formatted_timestamp', 'changes'
        ]
        read_only_fields = '__all__'
    
    def get_formatted_timestamp(self, obj):
        """Get formatted timestamp"""
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')


class SystemConfigurationSerializer(serializers.ModelSerializer):
    """System configuration serializer"""
    
    class Meta:
        model = SystemConfiguration
        fields = [
            'hospital_name', 'hospital_logo', 'contact_email', 'contact_phone', 'address',
            'consultation_fee', 'currency_code', 'tax_rate',
            'appointment_duration', 'advance_booking_days', 'cancellation_hours',
            'patient_id_prefix', 'auto_generate_patient_id',
            'email_notifications', 'sms_notifications', 'whatsapp_notifications',
            'auto_backup', 'backup_frequency', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'middle_name', 'last_name',
            'full_name', 'display_name', 'role', 'employee_id',
            'phone', 'alternate_phone', 'address', 'city', 'state', 'country', 'postal_code',
            'date_of_birth', 'gender', 'blood_group', 'specialization', 'qualification',
            'experience_years', 'license_number', 'joining_date',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
            'profile_picture', 'bio', 'hospital_name', 'department_name',
            'is_available', 'last_activity', 'date_joined'
        ]
        read_only_fields = [
            'id', 'username', 'role', 'employee_id', 'full_name', 'display_name',
            'hospital_name', 'department_name', 'date_joined', 'last_activity'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }


class FileUploadSerializer(serializers.ModelSerializer):
    """File upload serializer"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_url = serializers.CharField(source='file.url', read_only=True)
    formatted_file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = FileUpload
        fields = [
            'id', 'file', 'file_url', 'original_name', 'file_size', 'formatted_file_size',
            'content_type', 'description', 'is_public', 'created_at',
            'uploaded_by_name'
        ]
        read_only_fields = [
            'id', 'file_url', 'file_size', 'content_type', 'created_at',
            'uploaded_by_name', 'formatted_file_size'
        ]
    
    def get_formatted_file_size(self, obj):
        """Get human-readable file size"""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistics serializer"""
    overview = serializers.DictField(required=False)
    today = serializers.DictField(required=False)
    this_week = serializers.DictField(required=False)
    this_month = serializers.DictField(required=False)
    pending = serializers.DictField(required=False)
    my_stats = serializers.DictField(required=False)


class UserSearchSerializer(serializers.ModelSerializer):
    """Simplified user serializer for search results"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'display_name', 'role', 'specialization', 'profile_picture']
        read_only_fields = '__all__'
