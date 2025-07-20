from rest_framework import serializers
from .models import Activity
from users.serializers import UserListSerializer

class ActivityListSerializer(serializers.ModelSerializer):
    created_by = UserListSerializer(read_only=True)
    primary_goal = serializers.SerializerMethodField()
    related_goals = serializers.SerializerMethodField()
    all_goals = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = [
            'id', 'name', 'description', 'category', 'difficulty', 'instructions',
            'prerequisites', 'estimated_duration', 'primary_goal', 'related_goals',
            'all_goals', 'goal_contribution_weight', 'image_url', 'video_url',
            'is_active', 'created_by', 'completion_rate', 'created_at', 'updated_at'
        ]

    def get_primary_goal(self, obj):
        if obj.primary_goal:
            return {'id': obj.primary_goal.id, 'name': obj.primary_goal.name}
        return None
    
    def get_related_goals(self, obj):
        return [{'id': goal.id, 'name': goal.name} for goal in obj.related_goals.all()]
    
    def get_all_goals(self, obj):
        all_goals = []
        if obj.primary_goal:
            all_goals.append({'id': obj.primary_goal.id, 'name': obj.primary_goal.name})
        for goal in obj.related_goals.all():
            if goal.id not in [g['id'] for g in all_goals]:
                all_goals.append({'id': goal.id, 'name': goal.name})
        return all_goals
    
    def get_completion_rate(self, obj):
        """Return completion rate as a numeric value"""
        rate = obj.completion_rate
        if isinstance(rate, (int, float)):
            return float(rate)
        return 0.0 