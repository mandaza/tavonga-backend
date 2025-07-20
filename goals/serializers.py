from rest_framework import serializers
from .models import Goal
from users.serializers import UserListSerializer
from activities.serializers_common import ActivityListSerializer
from .serializers_common import GoalListSerializer

class GoalSerializer(serializers.ModelSerializer):
    created_by = UserListSerializer(read_only=True)
    assigned_carers = UserListSerializer(many=True, read_only=True)
    primary_activities = ActivityListSerializer(many=True, read_only=True)
    related_activities = ActivityListSerializer(many=True, read_only=True)
    all_activities = ActivityListSerializer(many=True, read_only=True)
    is_overdue = serializers.ReadOnlyField()
    calculated_progress = serializers.ReadOnlyField()
    completed_activities_count = serializers.ReadOnlyField()
    total_activities_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Goal
        fields = [
            'id', 'name', 'description', 'category', 'target_date', 'status',
            'priority', 'assigned_carers', 'created_by', 'progress_percentage',
            'calculated_progress', 'notes', 'required_activities_count',
            'completion_threshold', 'primary_activities', 'related_activities',
            'all_activities', 'completed_activities_count', 'total_activities_count',
            'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class GoalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = [
            'name', 'description', 'category', 'target_date', 'status',
            'priority', 'assigned_carers', 'progress_percentage', 'notes',
            'required_activities_count', 'completion_threshold'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class GoalUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = [
            'name', 'description', 'category', 'target_date', 'status',
            'priority', 'assigned_carers', 'progress_percentage', 'notes',
            'required_activities_count', 'completion_threshold'
        ]


class GoalProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = ['progress_percentage', 'notes']
    
    def validate_progress_percentage(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Progress percentage must be between 0 and 100")
        return value 