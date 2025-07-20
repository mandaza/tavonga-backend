from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Activity, ActivityLog
from .serializers import (
    ActivitySerializer, ActivityCreateSerializer, ActivityListSerializer,
    ActivityLogSerializer, ActivityLogCreateSerializer, ActivityLogUpdateSerializer,
    ActivityLogListSerializer
)

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "is_admin", False)

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'difficulty', 'primary_goal', 'created_by']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ActivityCreateSerializer
        elif self.action == 'list':
            return ActivityListSerializer
        return ActivitySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Activity.objects.none()
        
        if self.request.user.is_admin:
            return Activity.objects.all()
        return Activity.objects.filter(is_active=True)


class ActivityLogViewSet(viewsets.ModelViewSet):
    queryset = ActivityLog.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['activity', 'status', 'completed', 'date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ActivityLogCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ActivityLogUpdateSerializer
        elif self.action == 'list':
            return ActivityLogListSerializer
        return ActivityLogSerializer
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return ActivityLog.objects.none()
        
        if self.request.user.is_admin:
            return ActivityLog.objects.all()
        return ActivityLog.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_activities(self, request):
        logs = self.get_queryset()
        serializer = ActivityLogListSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        from django.utils import timezone
        today = timezone.now().date()
        logs = self.get_queryset().filter(date=today)
        serializer = ActivityLogListSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        logs = self.get_queryset().filter(status='scheduled')
        overdue_logs = [log for log in logs if log.is_overdue]
        serializer = ActivityLogListSerializer(overdue_logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Comprehensive activity analytics for Tavonga"""
        from django.db.models import Count, Avg, Q
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        queryset = self.get_queryset()
        
        # Activity completion statistics
        completion_stats = queryset.aggregate(
            total_activities=Count('id'),
            completed_activities=Count('id', filter=Q(completed=True)),
            in_progress_activities=Count('id', filter=Q(status='in_progress')),
            cancelled_activities=Count('id', filter=Q(status='cancelled'))
        )
        
        # Calculate completion rate
        completion_rate = (completion_stats['completed_activities'] / completion_stats['total_activities'] * 100) if completion_stats['total_activities'] > 0 else 0
        
        # Activity category performance
        category_performance = queryset.values('activity__category').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(completed=True))
        ).order_by('-completed')
        
        # Calculate completion rate in Python
        for category in category_performance:
            category['completion_rate'] = (category['completed'] / category['total'] * 100) if category['total'] > 0 else 0
        
        # Sort by completion rate
        category_performance = sorted(category_performance, key=lambda x: x['completion_rate'], reverse=True)
        
        # Difficulty level performance
        difficulty_performance = queryset.values('activity__difficulty').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(completed=True)),
            avg_satisfaction=Avg('satisfaction_rating', filter=Q(satisfaction_rating__isnull=False)),
            avg_difficulty_rating=Avg('difficulty_rating', filter=Q(difficulty_rating__isnull=False))
        ).order_by('-completed')
        
        # Calculate completion rate in Python
        for difficulty in difficulty_performance:
            difficulty['completion_rate'] = (difficulty['completed'] / difficulty['total'] * 100) if difficulty['total'] > 0 else 0
        
        # Sort by completion rate
        difficulty_performance = sorted(difficulty_performance, key=lambda x: x['completion_rate'], reverse=True)
        
        # Most successful activities
        successful_activities = queryset.filter(completed=True).values(
            'activity__name', 'activity__category', 'activity__id'
        ).annotate(
            completion_count=Count('id'),
            avg_satisfaction=Avg('satisfaction_rating', filter=Q(satisfaction_rating__isnull=False))
        ).order_by('-completion_count')[:10]
        
        # Most challenging activities
        challenging_activities = queryset.filter(
            Q(completed=False) | Q(difficulty_rating__gt=3)
        ).values(
            'activity__name', 'activity__category', 'activity__id'
        ).annotate(
            challenge_count=Count('id'),
            avg_difficulty_rating=Avg('difficulty_rating', filter=Q(difficulty_rating__isnull=False))
        ).order_by('-challenge_count')[:10]
        
        # Time-based completion patterns
        completion_by_day = queryset.filter(completed=True).extra(
            select={'day_of_week': "strftime('%%w', date)"}
        ).values('day_of_week').annotate(
            completion_count=Count('id')
        ).order_by('day_of_week')
        
        # Recent trends (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        recent_activities = queryset.filter(date__gte=thirty_days_ago)
        
        daily_completion_trend = []
        for day in range(30):
            date = thirty_days_ago + timedelta(days=day)
            day_stats = recent_activities.filter(date=date).aggregate(
                total=Count('id'),
                completed=Count('id', filter=Q(completed=True))
            )
            daily_completion_trend.append({
                'date': date,
                'total_activities': day_stats['total'],
                'completed_activities': day_stats['completed'],
                'completion_rate': (day_stats['completed'] / day_stats['total'] * 100) if day_stats['total'] > 0 else 0
            })
        
        return Response({
            'completion_statistics': completion_stats,
            'overall_completion_rate': round(completion_rate, 2),
            'category_performance': category_performance,
            'difficulty_performance': difficulty_performance,
            'successful_activities': successful_activities,
            'challenging_activities': challenging_activities,
            'completion_by_day': completion_by_day,
            'daily_completion_trend': daily_completion_trend
        })
    
    @action(detail=False, methods=['get'])
    def mastery_tracking(self, request):
        """Track Tavonga's mastery and skill development"""
        from django.db.models import Count, Avg, Q
        
        queryset = self.get_queryset()
        
        # Activity mastery analysis (activities completed multiple times with improving ratings)
        mastery_analysis = []
        activities = queryset.values('activity__id', 'activity__name').distinct()
        
        for activity in activities:
            activity_logs = queryset.filter(
                activity__id=activity['activity__id'],
                completed=True
            ).order_by('date')
            
            if activity_logs.count() >= 2:  # Need at least 2 completions to track improvement
                first_completion = activity_logs.first()
                latest_completion = activity_logs.last()
                
                # Calculate improvement metrics
                difficulty_improvement = 0
                satisfaction_improvement = 0
                
                if (first_completion.difficulty_rating and latest_completion.difficulty_rating):
                    difficulty_improvement = first_completion.difficulty_rating - latest_completion.difficulty_rating
                
                if (first_completion.satisfaction_rating and latest_completion.satisfaction_rating):
                    satisfaction_improvement = latest_completion.satisfaction_rating - first_completion.satisfaction_rating
                
                mastery_analysis.append({
                    'activity_id': activity['activity__id'],
                    'activity_name': activity['activity__name'],
                    'total_completions': activity_logs.count(),
                    'first_completion_date': first_completion.date,
                    'latest_completion_date': latest_completion.date,
                    'difficulty_improvement': difficulty_improvement,  # Positive = easier over time
                    'satisfaction_improvement': satisfaction_improvement,  # Positive = more satisfied over time
                    'mastery_level': 'advanced' if activity_logs.count() >= 5 and difficulty_improvement > 0 else 'developing'
                })
        
        # Sort by mastery level and improvement
        mastery_analysis.sort(key=lambda x: (x['mastery_level'] == 'advanced', x['total_completions']), reverse=True)
        
        # Skill categories where Tavonga excels
        excel_categories = queryset.filter(
            completed=True,
            satisfaction_rating__gte=4
        ).values('activity__category').annotate(
            high_satisfaction_count=Count('id'),
            avg_satisfaction=Avg('satisfaction_rating')
        ).order_by('-avg_satisfaction')
        
        # Goal-aligned activity progress
        goal_progress = queryset.filter(
            activity__primary_goal__isnull=False,
            completed=True
        ).values(
            'activity__primary_goal__name',
            'activity__primary_goal__id'
        ).annotate(
            activities_completed=Count('id'),
            avg_satisfaction=Avg('satisfaction_rating', filter=Q(satisfaction_rating__isnull=False))
        ).order_by('-activities_completed')
        
        return Response({
            'mastery_analysis': mastery_analysis,
            'excel_categories': excel_categories,
            'goal_aligned_progress': goal_progress,
            'skill_insights': [
                "Focus on activities where Tavonga shows consistent improvement",
                "Build on categories with high satisfaction ratings",
                "Gradually increase difficulty in mastered areas"
            ]
        })
