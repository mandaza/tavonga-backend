from rest_framework import serializers
from .models import Shift
from users.serializers import UserListSerializer

class ShiftSerializer(serializers.ModelSerializer):
    carer = UserListSerializer(read_only=True)
    assigned_by = UserListSerializer(read_only=True)
    duration_hours = serializers.ReadOnlyField()
    is_late = serializers.ReadOnlyField()
    is_early_leave = serializers.ReadOnlyField()
    is_current_shift = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Shift
        fields = [
            'id', 'carer', 'date', 'shift_type', 'start_time', 'end_time',
            'break_duration', 'clock_in', 'clock_out', 'clock_in_location',
            'clock_out_location', 'status', 'assigned_by', 'location',
            'client_name', 'client_address', 'notes', 'special_instructions',
            'emergency_contact', 'performance_rating', 'supervisor_notes',
            'duration_hours', 'is_late', 'is_early_leave', 'is_current_shift',
            'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'carer', 'assigned_by', 'created_at', 'updated_at']


class ShiftCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = [
            'carer', 'date', 'shift_type', 'start_time', 'end_time',
            'break_duration', 'location', 'client_name', 'client_address',
            'notes', 'special_instructions', 'emergency_contact'
        ]
    
    def create(self, validated_data):
        validated_data['assigned_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, attrs):
        # Validate that end_time is after start_time
        if attrs['end_time'] <= attrs['start_time']:
            raise serializers.ValidationError("End time must be after start time")
        
        # Validate that carer is not already assigned to a shift at the same time
        existing_shift = Shift.objects.filter(
            carer=attrs['carer'],
            date=attrs['date'],
            start_time__lt=attrs['end_time'],
            end_time__gt=attrs['start_time']
        ).exists()
        
        if existing_shift:
            raise serializers.ValidationError("Carer already has a shift scheduled during this time")
        
        return attrs


class ShiftUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = [
            'shift_type', 'start_time', 'end_time', 'break_duration',
            'location', 'client_name', 'client_address', 'notes',
            'special_instructions', 'emergency_contact', 'performance_rating',
            'supervisor_notes'
        ]
    
    def validate(self, attrs):
        if attrs.get('start_time') and attrs.get('end_time'):
            if attrs['end_time'] <= attrs['start_time']:
                raise serializers.ValidationError("End time must be after start time")
        return attrs


class ShiftListSerializer(serializers.ModelSerializer):
    carer = UserListSerializer(read_only=True)
    assigned_by = UserListSerializer(read_only=True)
    duration_hours = serializers.ReadOnlyField()
    is_late = serializers.ReadOnlyField()
    is_early_leave = serializers.ReadOnlyField()
    is_current_shift = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Shift
        fields = [
            'id', 'carer', 'date', 'shift_type', 'start_time', 'end_time',
            'status', 'clock_in', 'clock_out', 'assigned_by', 'location',
            'duration_hours', 'is_late', 'is_early_leave', 'is_current_shift',
            'is_overdue', 'created_at'
        ]


class ShiftClockInSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ['clock_in_location']
    
    def validate(self, attrs):
        shift = self.instance
        
        # Check if shift is already clocked in
        if shift.clock_in:
            raise serializers.ValidationError("Shift is already clocked in")
        
        # Check if shift is scheduled for today
        from django.utils import timezone
        today = timezone.now().date()
        if shift.date != today:
            raise serializers.ValidationError("Can only clock in for today's shift")
        
        return attrs
    
    def update(self, instance, validated_data):
        from django.utils import timezone
        instance.clock_in = timezone.now()
        instance.clock_in_location = validated_data.get('clock_in_location', '')
        instance.status = 'in_progress'
        instance.save()
        return instance


class ShiftClockOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ['clock_out_location', 'performance_rating', 'supervisor_notes']
    
    def validate(self, attrs):
        shift = self.instance
        
        # Check if shift is clocked in
        if not shift.clock_in:
            raise serializers.ValidationError("Must clock in before clocking out")
        
        # Check if already clocked out
        if shift.clock_out:
            raise serializers.ValidationError("Shift is already clocked out")
        
        return attrs
    
    def update(self, instance, validated_data):
        from django.utils import timezone
        instance.clock_out = timezone.now()
        instance.clock_out_location = validated_data.get('clock_out_location', '')
        instance.performance_rating = validated_data.get('performance_rating')
        instance.supervisor_notes = validated_data.get('supervisor_notes', '')
        instance.status = 'completed'
        instance.save()
        return instance


class ShiftScheduleSerializer(serializers.ModelSerializer):
    carer = UserListSerializer(read_only=True)
    is_current_shift = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Shift
        fields = [
            'id', 'carer', 'date', 'shift_type', 'start_time', 'end_time',
            'status', 'location', 'client_name', 'is_current_shift',
            'is_overdue', 'created_at'
        ] 