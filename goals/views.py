from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Goal
from .serializers import (
    GoalSerializer, GoalCreateSerializer, GoalUpdateSerializer,
    GoalListSerializer, GoalProgressSerializer
)

# Create your views here.

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "is_admin", False)

class IsAssignedCarerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (getattr(request.user, "is_admin", False) or request.user in obj.assigned_carers.all())

class GoalViewSet(viewsets.ModelViewSet):
    queryset = Goal.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'priority', 'category', 'created_by']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return GoalCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return GoalUpdateSerializer
        elif self.action == 'track_progress':
            return GoalProgressSerializer
        return GoalSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return [IsAssignedCarerOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Goal.objects.none()
        
        if self.request.user.is_admin:
            return Goal.objects.all()
        return Goal.objects.filter(assigned_carers=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def track_progress(self, request, pk=None):
        goal = self.get_object()
        serializer = GoalProgressSerializer(goal, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(GoalSerializer(goal).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_goals(self, request):
        goals = self.get_queryset()
        serializer = GoalListSerializer(goals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        if not request.user.is_admin:
            return Response(
                {'error': 'Only admins can view overdue goals'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        goals = Goal.objects.filter(status='active')
        overdue_goals = [goal for goal in goals if goal.is_overdue]
        serializer = GoalListSerializer(overdue_goals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Comprehensive goal analytics for Tavonga"""
        from django.db.models import Count, Avg, Q
        from activities.models import ActivityLog
        
        queryset = self.get_queryset()
        
        # Goal status distribution
        status_distribution = queryset.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Goal priority distribution
        priority_distribution = queryset.values('priority').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Goal category distribution
        category_distribution = queryset.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Progress statistics
        progress_stats = queryset.aggregate(
            avg_progress=Avg('progress_percentage'),
            total_goals=Count('id'),
            completed_goals=Count('id', filter=Q(status='completed')),
            active_goals=Count('id', filter=Q(status='active')),
            overdue_goals=Count('id', filter=Q(status='active'))  # Will need to filter overdue manually
        )
        
        # Calculate completion rate
        completion_rate = (progress_stats['completed_goals'] / progress_stats['total_goals'] * 100) if progress_stats['total_goals'] > 0 else 0
        
        # Most and least successful goals
        successful_goals = queryset.filter(progress_percentage__gte=80).order_by('-progress_percentage')[:5]
        struggling_goals = queryset.filter(status='active', progress_percentage__lt=50).order_by('progress_percentage')[:5]
        
        # Activity-goal relationships
        goal_activity_stats = []
        for goal in queryset:
            activities = goal.all_activities
            total_activities = len(activities)
            completed_activities = goal.completed_activities_count
            
            goal_activity_stats.append({
                'goal_id': goal.id,
                'goal_name': goal.name,
                'total_activities': total_activities,
                'completed_activities': completed_activities,
                'completion_rate': (completed_activities / total_activities * 100) if total_activities > 0 else 0,
                'progress_percentage': goal.progress_percentage
            })
        
        # Sort by completion rate
        goal_activity_stats.sort(key=lambda x: x['completion_rate'], reverse=True)
        
        return Response({
            'status_distribution': status_distribution,
            'priority_distribution': priority_distribution,
            'category_distribution': category_distribution,
            'progress_statistics': progress_stats,
            'completion_rate': round(completion_rate, 2),
            'successful_goals': [{
                'id': goal.id,
                'name': goal.name,
                'progress_percentage': goal.progress_percentage,
                'status': goal.status
            } for goal in successful_goals],
            'struggling_goals': [{
                'id': goal.id,
                'name': goal.name,
                'progress_percentage': goal.progress_percentage,
                'status': goal.status
            } for goal in struggling_goals],
            'goal_activity_relationships': goal_activity_stats
        })
    
    @action(detail=False, methods=['get'])
    def progress_trends(self, request):
        """Track goal progress trends over time"""
        from django.db.models import Count, Avg
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        queryset = self.get_queryset()
        
        # Get date range
        days_back = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Progress by week
        weekly_progress = []
        for week in range(4):  # Last 4 weeks
            week_end = end_date - timedelta(weeks=week)
            week_start = week_end - timedelta(days=6)
            
            # Get goals that were active during this week
            week_goals = queryset.filter(
                created_at__lte=week_end,
                status__in=['active', 'completed']
            )
            
            avg_progress = week_goals.aggregate(
                avg_progress=Avg('progress_percentage')
            )['avg_progress'] or 0
            
            weekly_progress.append({
                'week': week,
                'start_date': week_start,
                'end_date': week_end,
                'average_progress': round(avg_progress, 2),
                'total_goals': week_goals.count()
            })
        
        # Goals completed per month (last 6 months)
        monthly_completions = []
        for month in range(6):
            month_date = end_date.replace(day=1) - timedelta(days=month*30)
            completed_count = queryset.filter(
                status='completed',
                updated_at__year=month_date.year,
                updated_at__month=month_date.month
            ).count()
            
            monthly_completions.append({
                'month': month_date.month,
                'year': month_date.year,
                'month_name': month_date.strftime('%B %Y'),
                'completed_goals': completed_count
            })
        
        return Response({
            'weekly_progress': weekly_progress,
            'monthly_completions': monthly_completions,
            'date_range': {
                'start': start_date,
                'end': end_date,
                'days': days_back
            }
        })
