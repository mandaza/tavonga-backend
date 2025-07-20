from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, date, time
from .models import Schedule, ScheduleTemplate, ScheduleReminder, ScheduleConflict
from activities.serializers_common import ActivityListSerializer
from users.serializers import UserListSerializer


class ScheduleListSerializer(serializers.ModelSerializer):
    """Serializer for schedule list view with essential fields"""
    activity = ActivityListSerializer(read_only=True)
    assigned_user = UserListSerializer(read_only=True)
    created_by = UserListSerializer(read_only=True)
    is_overdue = serializers.ReadOnlyField()
    is_today = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    scheduled_datetime = serializers.ReadOnlyField()
    actual_duration_minutes = serializers.ReadOnlyField()
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'activity', 'assigned_user', 'created_by', 'scheduled_date',
            'scheduled_time', 'status', 'priority', 'completed', 'location',
            'is_overdue', 'is_today', 'is_upcoming', 'scheduled_datetime',
            'actual_duration_minutes', 'completion_percentage', 'created_at'
        ]


class ScheduleDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed schedule view with all fields"""
    activity = ActivityListSerializer(read_only=True)
    assigned_user = UserListSerializer(read_only=True)
    created_by = UserListSerializer(read_only=True)
    is_overdue = serializers.ReadOnlyField()
    is_today = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    scheduled_datetime = serializers.ReadOnlyField()
    actual_duration_minutes = serializers.ReadOnlyField()
    time_until_scheduled = serializers.ReadOnlyField()
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'activity', 'assigned_user', 'created_by', 'scheduled_date',
            'scheduled_time', 'estimated_duration', 'actual_start_time',
            'actual_end_time', 'status', 'priority', 'recurrence_type',
            'recurrence_end_date', 'parent_schedule', 'notes', 'preparation_notes',
            'completion_notes', 'location', 'special_requirements', 'send_reminder',
            'reminder_minutes_before', 'reminder_sent', 'completed',
            'completion_percentage', 'difficulty_rating', 'satisfaction_rating',
            'is_overdue', 'is_today', 'is_upcoming', 'scheduled_datetime',
            'actual_duration_minutes', 'time_until_scheduled', 'created_at', 'updated_at'
        ]


class ScheduleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new schedules"""
    
    class Meta:
        model = Schedule
        fields = [
            'activity', 'assigned_user', 'scheduled_date', 'scheduled_time',
            'estimated_duration', 'priority', 'recurrence_type', 'recurrence_end_date',
            'notes', 'preparation_notes', 'location', 'special_requirements',
            'send_reminder', 'reminder_minutes_before'
        ]
    
    def validate_scheduled_date(self, value):
        """Validate that scheduled date is not in the past"""
        if value < timezone.now().date():
            raise serializers.ValidationError("Scheduled date cannot be in the past")
        return value
    
    def validate_recurrence_end_date(self, value):
        """Validate recurrence end date"""
        if value and value < timezone.now().date():
            raise serializers.ValidationError("Recurrence end date cannot be in the past")
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        # If recurrence is set, ensure end date is provided and after start date
        if attrs.get('recurrence_type') and attrs['recurrence_type'] != 'none':
            if not attrs.get('recurrence_end_date'):
                raise serializers.ValidationError({
                    'recurrence_end_date': 'Recurrence end date is required when recurrence is set'
                })
            if attrs['recurrence_end_date'] <= attrs['scheduled_date']:
                raise serializers.ValidationError({
                    'recurrence_end_date': 'Recurrence end date must be after scheduled date'
                })
        
        # Check for scheduling conflicts (same user, overlapping time)
        scheduled_datetime = timezone.make_aware(
            datetime.combine(attrs['scheduled_date'], attrs['scheduled_time'])
        )
        
        # Check if user already has a schedule at this time
        existing_schedules = Schedule.objects.filter(
            assigned_user=attrs['assigned_user'],
            scheduled_date=attrs['scheduled_date'],
            status__in=['scheduled', 'in_progress']
        )
        
        if self.instance:
            existing_schedules = existing_schedules.exclude(id=self.instance.id)
        
        for schedule in existing_schedules:
            existing_datetime = schedule.scheduled_datetime
            duration = attrs.get('estimated_duration', 60)  # Default 60 minutes
            existing_duration = schedule.estimated_duration or 60
            
            # Check for time overlap
            new_end = scheduled_datetime + timezone.timedelta(minutes=duration)
            existing_end = existing_datetime + timezone.timedelta(minutes=existing_duration)
            
            if (scheduled_datetime < existing_end and new_end > existing_datetime):
                raise serializers.ValidationError({
                    'scheduled_time': f'Time conflict with existing schedule: {schedule.activity.name} at {schedule.scheduled_time}'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create schedule and handle recurrence"""
        validated_data['created_by'] = self.context['request'].user
        
        # Create the main schedule
        schedule = Schedule.objects.create(**validated_data)
        
        # Handle recurrence
        if validated_data.get('recurrence_type') and validated_data['recurrence_type'] != 'none':
            self._create_recurring_schedules(schedule, validated_data)
        
        return schedule
    
    def _create_recurring_schedules(self, parent_schedule, validated_data):
        """Create recurring schedules based on recurrence type"""
        recurrence_type = validated_data['recurrence_type']
        end_date = validated_data['recurrence_end_date']
        current_date = validated_data['scheduled_date']
        
        while current_date < end_date:
            if recurrence_type == 'daily':
                current_date += timezone.timedelta(days=1)
            elif recurrence_type == 'weekly':
                current_date += timezone.timedelta(weeks=1)
            elif recurrence_type == 'monthly':
                # Add one month (approximately)
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            if current_date <= end_date:
                Schedule.objects.create(
                    activity=parent_schedule.activity,
                    assigned_user=parent_schedule.assigned_user,
                    created_by=parent_schedule.created_by,
                    scheduled_date=current_date,
                    scheduled_time=parent_schedule.scheduled_time,
                    estimated_duration=parent_schedule.estimated_duration,
                    priority=parent_schedule.priority,
                    notes=parent_schedule.notes,
                    preparation_notes=parent_schedule.preparation_notes,
                    location=parent_schedule.location,
                    special_requirements=parent_schedule.special_requirements,
                    send_reminder=parent_schedule.send_reminder,
                    reminder_minutes_before=parent_schedule.reminder_minutes_before,
                    parent_schedule=parent_schedule,
                    recurrence_type='none'  # Recurring instances don't recurse further
                )


class ScheduleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating schedules"""
    
    class Meta:
        model = Schedule
        fields = [
            'activity', 'assigned_user', 'scheduled_date', 'scheduled_time', 
            'estimated_duration', 'status', 'priority', 'notes', 'preparation_notes', 
            'completion_notes', 'location', 'special_requirements', 'send_reminder',
            'reminder_minutes_before', 'completed', 'completion_percentage',
            'difficulty_rating', 'satisfaction_rating'
        ]
    
    def validate_difficulty_rating(self, value):
        """Validate difficulty rating range"""
        if value and (value < 1 or value > 5):
            raise serializers.ValidationError("Difficulty rating must be between 1 and 5")
        return value
    
    def validate_satisfaction_rating(self, value):
        """Validate satisfaction rating range"""
        if value and (value < 1 or value > 5):
            raise serializers.ValidationError("Satisfaction rating must be between 1 and 5")
        return value
    
    def validate_completion_percentage(self, value):
        """Validate completion percentage range"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Completion percentage must be between 0 and 100")
        return value
    
    def validate_scheduled_date(self, value):
        """Validate that scheduled date is not in the past (for new schedules)"""
        if value < timezone.now().date():
            raise serializers.ValidationError("Scheduled date cannot be in the past")
        return value


class ScheduleTemplateSerializer(serializers.ModelSerializer):
    """Serializer for schedule templates"""
    activity = ActivityListSerializer(read_only=True)
    created_by = UserListSerializer(read_only=True)
    
    class Meta:
        model = ScheduleTemplate
        fields = [
            'id', 'name', 'description', 'activity', 'default_duration',
            'default_priority', 'default_location', 'default_preparation_notes',
            'default_reminder_minutes', 'created_by', 'created_at', 'updated_at'
        ]


class ScheduleTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating schedule templates"""
    
    class Meta:
        model = ScheduleTemplate
        fields = [
            'name', 'description', 'activity', 'default_duration',
            'default_priority', 'default_location', 'default_preparation_notes',
            'default_reminder_minutes'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ScheduleConflictSerializer(serializers.ModelSerializer):
    """Serializer for schedule conflicts"""
    schedule1 = ScheduleListSerializer(read_only=True)
    schedule2 = ScheduleListSerializer(read_only=True)
    
    class Meta:
        model = ScheduleConflict
        fields = [
            'id', 'schedule1', 'schedule2', 'conflict_type', 'resolved',
            'resolution_notes', 'created_at', 'resolved_at'
        ]


class ScheduleReminderSerializer(serializers.ModelSerializer):
    """Serializer for schedule reminders"""
    schedule = ScheduleListSerializer(read_only=True)
    
    class Meta:
        model = ScheduleReminder
        fields = [
            'id', 'schedule', 'reminder_type', 'sent_at', 'delivered', 'opened'
        ]


class ScheduleQuickActionSerializer(serializers.Serializer):
    """Serializer for quick schedule actions like start, complete, cancel"""
    action = serializers.ChoiceField(choices=['start', 'complete', 'cancel'])
    completion_percentage = serializers.IntegerField(required=False, min_value=0, max_value=100)
    completion_notes = serializers.CharField(required=False, allow_blank=True)
    difficulty_rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    satisfaction_rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    cancel_reason = serializers.CharField(required=False, allow_blank=True)


class ScheduleRescheduleSerializer(serializers.Serializer):
    """Serializer for rescheduling"""
    new_date = serializers.DateField()
    new_time = serializers.TimeField()
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_new_date(self, value):
        """Validate that new date is not in the past"""
        if value < timezone.now().date():
            raise serializers.ValidationError("New date cannot be in the past")
        return value 