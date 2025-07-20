from rest_framework import serializers
from .models import BehaviorLog
from users.serializers import UserListSerializer
from media.serializers import MediaFileSerializer
from activities.serializers_common import ActivityListSerializer

class BehaviorLogSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    related_activity = ActivityListSerializer(read_only=True)
    is_critical = serializers.ReadOnlyField()
    requires_immediate_attention = serializers.ReadOnlyField()
    is_activity_related = serializers.ReadOnlyField()
    activity_context = serializers.ReadOnlyField()
    media = MediaFileSerializer(many=True, read_only=True)
    
    class Meta:
        model = BehaviorLog
        fields = [
            'id', 'user', 'date', 'time', 'location', 'specific_location',
            'related_activity', 'related_activity_log', 'behavior_occurrence',
            'activity_before', 'behavior_type', 'behaviors', 'warning_signs',
            'duration_minutes', 'severity', 'harm_to_self', 'harm_to_others',
            'property_damage', 'damage_description', 'intervention_used',
            'intervention_effective', 'intervention_notes', 'follow_up_required',
            'follow_up_notes', 'photos', 'videos', 'notes', 'triggers_identified',
            'is_critical', 'requires_immediate_attention', 'is_activity_related',
            'activity_context', 'media', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class BehaviorLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehaviorLog
        fields = [
            'date', 'time', 'location', 'specific_location', 'related_activity',
            'related_activity_log', 'behavior_occurrence', 'activity_before',
            'behavior_type', 'behaviors', 'warning_signs', 'duration_minutes',
            'severity', 'harm_to_self', 'harm_to_others', 'property_damage',
            'damage_description', 'intervention_used', 'intervention_effective',
            'intervention_notes', 'follow_up_required', 'follow_up_notes',
            'photos', 'videos', 'notes', 'triggers_identified'
        ]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        # Validate that if related_activity_log is provided, it matches related_activity
        if data.get('related_activity_log') and data.get('related_activity'):
            if data['related_activity_log'].activity != data['related_activity']:
                raise serializers.ValidationError(
                    "The related_activity_log must belong to the specified related_activity"
                )
        
        # Auto-set related_activity if only related_activity_log is provided
        if data.get('related_activity_log') and not data.get('related_activity'):
            data['related_activity'] = data['related_activity_log'].activity
        
        return data


class BehaviorLogUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehaviorLog
        fields = [
            'location', 'specific_location', 'related_activity', 'related_activity_log',
            'behavior_occurrence', 'activity_before', 'behavior_type',
            'behaviors', 'warning_signs', 'duration_minutes', 'severity',
            'harm_to_self', 'harm_to_others', 'property_damage', 'damage_description',
            'intervention_used', 'intervention_effective', 'intervention_notes',
            'follow_up_required', 'follow_up_notes', 'photos', 'videos',
            'notes', 'triggers_identified'
        ]
    
    def validate(self, data):
        # Same validation logic as create
        if data.get('related_activity_log') and data.get('related_activity'):
            if data['related_activity_log'].activity != data['related_activity']:
                raise serializers.ValidationError(
                    "The related_activity_log must belong to the specified related_activity"
                )
        
        if data.get('related_activity_log') and not data.get('related_activity'):
            data['related_activity'] = data['related_activity_log'].activity
        
        return data


class BehaviorLogListSerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    related_activity = ActivityListSerializer(read_only=True)
    is_critical = serializers.ReadOnlyField()
    requires_immediate_attention = serializers.ReadOnlyField()
    is_activity_related = serializers.ReadOnlyField()
    
    class Meta:
        model = BehaviorLog
        fields = [
            'id', 'user', 'date', 'time', 'behavior_type', 'severity',
            'location', 'duration_minutes', 'harm_to_self', 'harm_to_others',
            'property_damage', 'related_activity', 'behavior_occurrence',
            'is_critical', 'requires_immediate_attention', 'is_activity_related',
            'created_at'
        ]


class BehaviorLogSummarySerializer(serializers.ModelSerializer):
    user = UserListSerializer(read_only=True)
    related_activity = ActivityListSerializer(read_only=True)
    
    class Meta:
        model = BehaviorLog
        fields = [
            'id', 'user', 'date', 'behavior_type', 'severity', 'location',
            'related_activity', 'behavior_occurrence', 'intervention_effective', 'created_at'
        ] 