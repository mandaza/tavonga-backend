from rest_framework import serializers
from .models import Goal
from users.serializers import UserListSerializer

class GoalListSerializer(serializers.ModelSerializer):
    created_by = UserListSerializer(read_only=True)
    assigned_carers_count = serializers.SerializerMethodField()
    activities_count = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = Goal
        fields = [
            'id', 'name', 'category', 'status', 'priority', 'target_date',
            'progress_percentage', 'created_by', 'assigned_carers_count',
            'activities_count', 'is_overdue', 'created_at'
        ]

    def get_assigned_carers_count(self, obj):
        return obj.assigned_carers.count()

    def get_activities_count(self, obj):
        return obj.total_activities_count 