from rest_framework import serializers
from .models import Activity, ActivityLog
from users.serializers import UserListSerializer
from goals.serializers_common import GoalListSerializer
from media.serializers import MediaFileSerializer
from .serializers_common import ActivityListSerializer

class ActivitySerializer(serializers.ModelSerializer):
    created_by = UserListSerializer(read_only=True)
    primary_goal = GoalListSerializer(read_only=True)
    related_goals = GoalListSerializer(many=True, read_only=True)
    all_goals = GoalListSerializer(many=True, read_only=True)
    completion_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = Activity
        fields = [
            'id', 'name', 'description', 'category', 'difficulty', 'instructions',
            'prerequisites', 'estimated_duration', 'primary_goal', 'related_goals',
            'all_goals', 'goal_contribution_weight', 'image_url', 'video_url',
            'is_active', 'created_by', 'completion_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class ActivityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = [
            'name', 'description', 'category', 'difficulty', 'instructions',
            'prerequisites', 'estimated_duration', 'primary_goal', 'related_goals',
            'goal_contribution_weight', 'image_url', 'video_url', 'is_active'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ActivityLogSerializer(serializers.ModelSerializer):
    activity = ActivityListSerializer(read_only=True)
    user = UserListSerializer(read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    media = MediaFileSerializer(many=True, read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'activity', 'user', 'date', 'scheduled_time', 'start_time',
            'end_time', 'status', 'completed', 'completion_notes',
            'difficulty_rating', 'satisfaction_rating', 'photos', 'videos',
            'notes', 'challenges', 'successes', 'duration_minutes', 'is_overdue',
            'media', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ActivityLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = [
            'activity', 'date', 'scheduled_time', 'status', 'notes'
        ]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ActivityLogUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityLog
        fields = [
            'status', 'start_time', 'end_time', 'completed', 'completion_notes',
            'difficulty_rating', 'satisfaction_rating', 'photos', 'videos',
            'notes', 'challenges', 'successes'
        ]
    
    def validate(self, attrs):
        # Validate that end_time is after start_time if both are provided
        if attrs.get('start_time') and attrs.get('end_time'):
            if attrs['end_time'] <= attrs['start_time']:
                raise serializers.ValidationError("End time must be after start time")
        
        # Validate rating ranges
        if attrs.get('difficulty_rating') and (attrs['difficulty_rating'] < 1 or attrs['difficulty_rating'] > 5):
            raise serializers.ValidationError("Difficulty rating must be between 1 and 5")
        
        if attrs.get('satisfaction_rating') and (attrs['satisfaction_rating'] < 1 or attrs['satisfaction_rating'] > 5):
            raise serializers.ValidationError("Satisfaction rating must be between 1 and 5")
        
        return attrs


class ActivityLogListSerializer(serializers.ModelSerializer):
    activity = ActivityListSerializer(read_only=True)
    user = UserListSerializer(read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'activity', 'user', 'date', 'scheduled_time', 'status',
            'completed', 'duration_minutes', 'is_overdue', 'created_at'
        ] 