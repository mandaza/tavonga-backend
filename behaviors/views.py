from django.shortcuts import render
from django.db.models import Q, Count, Avg
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import BehaviorLog
from .serializers import (
    BehaviorLogSerializer, BehaviorLogCreateSerializer, BehaviorLogUpdateSerializer,
    BehaviorLogListSerializer, BehaviorLogSummarySerializer
)

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "is_admin", False)

class BehaviorLogViewSet(viewsets.ModelViewSet):
    queryset = BehaviorLog.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'behavior_type', 'severity', 'location', 'date', 'user', 
        'related_activity', 'behavior_occurrence'
    ]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BehaviorLogCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BehaviorLogUpdateSerializer
        elif self.action == 'list':
            return BehaviorLogListSerializer
        elif self.action == 'summary':
            return BehaviorLogSummarySerializer
        return BehaviorLogSerializer
    
    def get_permissions(self):
        if self.action in ['destroy']:
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return BehaviorLog.objects.none()
        
        if self.request.user.is_admin:
            return BehaviorLog.objects.all()
        return BehaviorLog.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_behaviors(self, request):
        logs = self.get_queryset()
        serializer = BehaviorLogListSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def critical(self, request):
        logs = self.get_queryset().filter(severity='critical')
        serializer = BehaviorLogListSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        logs = self.get_queryset()
        serializer = BehaviorLogSummarySerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        from django.utils import timezone
        today = timezone.now().date()
        logs = self.get_queryset().filter(date=today)
        serializer = BehaviorLogListSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def activity_related(self, request):
        """Get all behavior logs that are related to activities"""
        logs = self.get_queryset().filter(
            Q(related_activity__isnull=False) | Q(related_activity_log__isnull=False)
        )
        serializer = BehaviorLogListSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def activity_triggers(self, request):
        """Get behavior logs that occurred during or immediately after activities"""
        logs = self.get_queryset().filter(
            behavior_occurrence__in=['during_activity', 'after_activity']
        )
        serializer = BehaviorLogListSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def activity_analytics(self, request):
        """Get analytics about activity-behavior relationships"""
        queryset = self.get_queryset()
        
        # Total behavior logs
        total_behaviors = queryset.count()
        
        # Activity-related behaviors
        activity_related = queryset.filter(
            Q(related_activity__isnull=False) | Q(related_activity_log__isnull=False)
        ).count()
        
        # Behaviors by occurrence type
        occurrence_stats = queryset.values('behavior_occurrence').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Most problematic activities (activities with most behavior incidents)
        activity_stats = queryset.filter(
            related_activity__isnull=False
        ).values(
            'related_activity__id',
            'related_activity__name',
            'related_activity__category'
        ).annotate(
            behavior_count=Count('id'),
            avg_severity=Avg('severity')
        ).order_by('-behavior_count')[:10]
        
        # Behavior types by activity context
        behavior_by_context = queryset.filter(
            related_activity__isnull=False
        ).values(
            'behavior_type', 'behavior_occurrence'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_behaviors': total_behaviors,
            'activity_related_behaviors': activity_related,
            'activity_related_percentage': round((activity_related / total_behaviors * 100) if total_behaviors > 0 else 0, 2),
            'occurrence_statistics': occurrence_stats,
            'problematic_activities': activity_stats,
            'behavior_by_context': behavior_by_context
        })
    
    @action(detail=False, methods=['get'])
    def activity_recommendations(self, request):
        """Get recommendations for activities based on behavior patterns"""
        queryset = self.get_queryset()
        
        # Activities that frequently trigger behaviors
        high_risk_activities = queryset.filter(
            related_activity__isnull=False,
            behavior_occurrence__in=['during_activity', 'after_activity']
        ).values(
            'related_activity__id',
            'related_activity__name',
            'related_activity__category'
        ).annotate(
            behavior_count=Count('id'),
            critical_count=Count('id', filter=Q(severity='critical'))
        ).filter(behavior_count__gt=1).order_by('-behavior_count')
        
        # Activities with successful interventions
        successful_activities = queryset.filter(
            related_activity__isnull=False,
            intervention_effective=True
        ).values(
            'related_activity__id',
            'related_activity__name',
            'related_activity__category'
        ).annotate(
            success_count=Count('id')
        ).order_by('-success_count')
        
        return Response({
            'high_risk_activities': high_risk_activities,
            'successful_intervention_activities': successful_activities,
            'recommendations': [
                "Consider modifying high-risk activities or providing additional support",
                "Replicate successful intervention strategies across similar activities",
                "Monitor behavior patterns during specific activity types",
                "Adjust activity schedules based on behavior occurrence patterns"
            ]
        })
    
    @action(detail=False, methods=['get'])
    def temporal_patterns(self, request):
        """Get temporal patterns for Tavonga's behavior analysis"""
        from django.db.models import Count, Avg
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        queryset = self.get_queryset()
        
        # Get date range from request
        days_back = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Filter by date range
        queryset = queryset.filter(date__gte=start_date, date__lte=end_date)
        
        # Hourly patterns
        hourly_data = []
        for hour in range(24):
            count = queryset.filter(time__hour=hour).count()
            hourly_data.append({
                'hour': hour,
                'count': count,
                'percentage': round((count / queryset.count() * 100) if queryset.count() > 0 else 0, 2)
            })
        
        # Daily patterns (by day of week)
        daily_data = []
        for day in range(7):  # 0 = Monday, 6 = Sunday
            count = queryset.filter(date__week_day=day+2).count()  # Django uses 1=Sunday, 2=Monday
            daily_data.append({
                'day': day,
                'day_name': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day],
                'count': count,
                'percentage': round((count / queryset.count() * 100) if queryset.count() > 0 else 0, 2)
            })
        
        # Weekly patterns (last 12 weeks)
        weekly_data = []
        for week in range(12):
            week_start = end_date - timedelta(weeks=week, days=end_date.weekday())
            week_end = week_start + timedelta(days=6)
            count = queryset.filter(date__gte=week_start, date__lte=week_end).count()
            weekly_data.append({
                'week': week,
                'start_date': week_start,
                'end_date': week_end,
                'count': count
            })
        
        # Monthly patterns (last 12 months)
        monthly_data = []
        for month in range(12):
            month_date = end_date.replace(day=1) - timedelta(days=month*30)
            count = queryset.filter(date__year=month_date.year, date__month=month_date.month).count()
            monthly_data.append({
                'month': month_date.month,
                'year': month_date.year,
                'month_name': month_date.strftime('%B %Y'),
                'count': count
            })
        
        # Duration analysis
        duration_stats = queryset.filter(duration_minutes__isnull=False).aggregate(
            avg_duration=Avg('duration_minutes'),
            total_behaviors=Count('id')
        )
        
        return Response({
            'temporal_patterns': {
                'hourly': hourly_data,
                'daily': daily_data,
                'weekly': weekly_data,
                'monthly': monthly_data
            },
            'duration_stats': duration_stats,
            'date_range': {
                'start': start_date,
                'end': end_date,
                'days': days_back
            }
        })
    
    @action(detail=False, methods=['get'])
    def trigger_analysis(self, request):
        """Comprehensive trigger analysis for Tavonga"""
        from django.db.models import Count, Q
        
        queryset = self.get_queryset()
        
        # Activity-behavior correlations
        activity_triggers = queryset.filter(
            related_activity__isnull=False
        ).values(
            'related_activity__name',
            'related_activity__category',
            'behavior_occurrence',
            'behavior_type'
        ).annotate(
            count=Count('id'),
            severity_avg=Avg('severity')
        ).order_by('-count')
        
        # Environmental triggers
        location_triggers = queryset.values('location', 'behavior_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Time-based triggers
        time_triggers = queryset.extra(
            select={'hour': 'EXTRACT(hour FROM time)'}
        ).values('hour', 'behavior_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Identified triggers analysis
        trigger_patterns = []
        for log in queryset.filter(triggers_identified__isnull=False):
            if isinstance(log.triggers_identified, list):
                for trigger in log.triggers_identified:
                    trigger_patterns.append({
                        'trigger': trigger,
                        'behavior_type': log.behavior_type,
                        'severity': log.severity,
                        'date': log.date
                    })
        
        # Group triggers by frequency
        trigger_frequency = {}
        for pattern in trigger_patterns:
            trigger = pattern['trigger']
            if trigger in trigger_frequency:
                trigger_frequency[trigger] += 1
            else:
                trigger_frequency[trigger] = 1
        
        # Convert to sorted list
        sorted_triggers = sorted(trigger_frequency.items(), key=lambda x: x[1], reverse=True)
        
        return Response({
            'activity_triggers': activity_triggers,
            'location_triggers': location_triggers,
            'time_triggers': time_triggers,
            'identified_triggers': sorted_triggers,
            'trigger_patterns': trigger_patterns[:50]  # Limit to recent 50
        })
    
    @action(detail=False, methods=['get'])
    def intervention_effectiveness(self, request):
        """Analyze intervention effectiveness for Tavonga"""
        from django.db.models import Count, Q, Avg
        
        queryset = self.get_queryset()
        
        # Overall intervention effectiveness
        interventions_with_outcome = queryset.filter(intervention_effective__isnull=False)
        total_interventions = interventions_with_outcome.count()
        successful_interventions = interventions_with_outcome.filter(intervention_effective=True).count()
        
        overall_success_rate = (successful_interventions / total_interventions * 100) if total_interventions > 0 else 0
        
        # Success rate by intervention type
        intervention_types = interventions_with_outcome.values('intervention_used').annotate(
            total=Count('id'),
            successful=Count('id', filter=Q(intervention_effective=True)),
            success_rate=Avg('intervention_effective')
        ).order_by('-success_rate')
        
        # Success rate by behavior type
        behavior_intervention_success = interventions_with_outcome.values('behavior_type').annotate(
            total=Count('id'),
            successful=Count('id', filter=Q(intervention_effective=True)),
            success_rate=Avg('intervention_effective')
        ).order_by('-success_rate')
        
        # Success rate by severity
        severity_success = interventions_with_outcome.values('severity').annotate(
            total=Count('id'),
            successful=Count('id', filter=Q(intervention_effective=True)),
            success_rate=Avg('intervention_effective')
        ).order_by('-success_rate')
        
        # Success rate by support worker
        worker_success = interventions_with_outcome.values(
            'user__first_name', 'user__last_name', 'user__id'
        ).annotate(
            total=Count('id'),
            successful=Count('id', filter=Q(intervention_effective=True)),
            success_rate=Avg('intervention_effective')
        ).order_by('-success_rate')
        
        # Best practices (most successful interventions)
        best_practices = queryset.filter(
            intervention_effective=True,
            intervention_notes__isnull=False
        ).exclude(intervention_notes='').values(
            'intervention_used', 'intervention_notes', 'behavior_type'
        ).annotate(
            usage_count=Count('id')
        ).order_by('-usage_count')[:10]
        
        return Response({
            'overall_success_rate': round(overall_success_rate, 2),
            'total_interventions': total_interventions,
            'successful_interventions': successful_interventions,
            'intervention_types': intervention_types,
            'behavior_success_rates': behavior_intervention_success,
            'severity_success_rates': severity_success,
            'worker_success_rates': worker_success,
            'best_practices': best_practices
        })
    
    @action(detail=False, methods=['get'])
    def worker_analysis(self, request):
        """Analyze support worker performance and patterns"""
        from django.db.models import Count, Avg, Q
        
        queryset = self.get_queryset()
        
        # Worker performance metrics
        worker_stats = queryset.values(
            'user__first_name', 'user__last_name', 'user__id'
        ).annotate(
            total_incidents=Count('id'),
            critical_incidents=Count('id', filter=Q(severity='critical')),
            high_severity_incidents=Count('id', filter=Q(severity='high')),
            avg_duration=Avg('duration_minutes', filter=Q(duration_minutes__isnull=False)),
            intervention_success_rate=Avg('intervention_effective', filter=Q(intervention_effective__isnull=False))
        ).order_by('-total_incidents')
        
        # Worker-specific behavior patterns
        worker_behavior_patterns = queryset.values(
            'user__first_name', 'user__last_name', 'behavior_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Worker intervention preferences
        worker_interventions = queryset.values(
            'user__first_name', 'user__last_name', 'intervention_used'
        ).annotate(
            count=Count('id'),
            success_rate=Avg('intervention_effective', filter=Q(intervention_effective__isnull=False))
        ).order_by('-count')
        
        # Most effective worker-intervention combinations
        effective_combinations = queryset.filter(
            intervention_effective=True
        ).values(
            'user__first_name', 'user__last_name', 'intervention_used', 'behavior_type'
        ).annotate(
            success_count=Count('id')
        ).order_by('-success_count')[:20]
        
        return Response({
            'worker_performance': worker_stats,
            'behavior_patterns': worker_behavior_patterns,
            'intervention_preferences': worker_interventions,
            'effective_combinations': effective_combinations
        })
    
    @action(detail=False, methods=['get'])
    def predictive_indicators(self, request):
        """Identify predictive indicators for behavior escalation"""
        from django.db.models import Count, Q
        from datetime import timedelta
        
        queryset = self.get_queryset()
        
        # Warning signs analysis
        warning_signs = []
        for log in queryset.filter(warning_signs__isnull=False):
            if isinstance(log.warning_signs, list):
                for sign in log.warning_signs:
                    warning_signs.append({
                        'warning_sign': sign,
                        'behavior_type': log.behavior_type,
                        'severity': log.severity,
                        'escalated': log.severity in ['high', 'critical']
                    })
        
        # Group warning signs by escalation likelihood
        warning_sign_analysis = {}
        for sign in warning_signs:
            sign_text = sign['warning_sign']
            if sign_text not in warning_sign_analysis:
                warning_sign_analysis[sign_text] = {
                    'total_occurrences': 0,
                    'escalated_occurrences': 0,
                    'escalation_rate': 0
                }
            
            warning_sign_analysis[sign_text]['total_occurrences'] += 1
            if sign['escalated']:
                warning_sign_analysis[sign_text]['escalated_occurrences'] += 1
        
        # Calculate escalation rates
        for sign_text, data in warning_sign_analysis.items():
            if data['total_occurrences'] > 0:
                data['escalation_rate'] = (data['escalated_occurrences'] / data['total_occurrences']) * 100
        
        # Sort by escalation rate
        sorted_warning_signs = sorted(
            warning_sign_analysis.items(), 
            key=lambda x: x[1]['escalation_rate'], 
            reverse=True
        )
        
        # Time-based patterns (behaviors that tend to cluster)
        time_clusters = queryset.values('date').annotate(
            behavior_count=Count('id'),
            severity_avg=Avg('severity')
        ).filter(behavior_count__gt=1).order_by('-behavior_count')
        
        return Response({
            'warning_signs': sorted_warning_signs,
            'time_clusters': time_clusters,
            'predictive_insights': [
                "Monitor for early warning signs with high escalation rates",
                "Be extra vigilant on days with multiple incidents",
                "Implement proactive strategies during high-risk time periods"
            ]
        })
    
    @action(detail=False, methods=['get'])
    def current_trends(self, request):
        """Get current behavior trends for dashboard - real-time analytics"""
        from django.db.models import Count, Avg, Q
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        queryset = self.get_queryset()
        now = timezone.now()
        today = now.date()
        
        # Get parameters for customization
        days_back = int(request.query_params.get('days', 7))  # Default to last 7 days
        
        # Date ranges
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        start_date = today - timedelta(days=days_back)
        
        # Current day stats
        today_behaviors = queryset.filter(date=today)
        today_count = today_behaviors.count()
        today_critical = today_behaviors.filter(severity='critical').count()
        
        # This week vs last week comparison
        this_week = queryset.filter(date__gte=week_ago, date__lte=today)
        last_week = queryset.filter(
            date__gte=week_ago - timedelta(days=7), 
            date__lt=week_ago
        )
        
        this_week_count = this_week.count()
        last_week_count = last_week.count()
        week_trend = ((this_week_count - last_week_count) / last_week_count * 100) if last_week_count > 0 else 0
        
        # Daily breakdown for the requested period
        daily_data = []
        for i in range(days_back):
            date = start_date + timedelta(days=i)
            day_behaviors = queryset.filter(date=date)
            daily_data.append({
                'date': date,
                'total': day_behaviors.count(),
                'critical': day_behaviors.filter(severity='critical').count(),
                'high': day_behaviors.filter(severity='high').count(),
                'medium': day_behaviors.filter(severity='medium').count(),
                'low': day_behaviors.filter(severity='low').count(),
                'day_name': date.strftime('%A'),
                'day_short': date.strftime('%a')
            })
        
        # Behavior type trends (last 7 days)
        type_trends = this_week.values('behavior_type').annotate(
            count=Count('id'),
            avg_severity=Avg('severity')
        ).order_by('-count')
        
        # Severity distribution (current period)
        severity_stats = queryset.filter(date__gte=start_date).aggregate(
            critical=Count('id', filter=Q(severity='critical')),
            high=Count('id', filter=Q(severity='high')),
            medium=Count('id', filter=Q(severity='medium')),
            low=Count('id', filter=Q(severity='low'))
        )
        
        # Intervention success rate (recent trends)
        recent_interventions = queryset.filter(
            date__gte=start_date,
            intervention_effective__isnull=False
        )
        total_interventions = recent_interventions.count()
        successful_interventions = recent_interventions.filter(intervention_effective=True).count()
        intervention_success_rate = (successful_interventions / total_interventions * 100) if total_interventions > 0 else 0
        
        # Peak hours analysis (current week)
        hourly_patterns = []
        for hour in range(24):
            hour_count = this_week.filter(time__hour=hour).count()
            hourly_patterns.append({
                'hour': hour,
                'count': hour_count,
                'hour_display': f"{hour:02d}:00"
            })
        
        # Critical alerts (needs immediate attention)
        critical_alerts = []
        
        # Check for spike in behaviors today
        if today_count > 0:
            avg_daily = queryset.filter(date__gte=month_ago).count() / 30
            if today_count > avg_daily * 2:  # More than 2x average
                critical_alerts.append({
                    'type': 'spike',
                    'message': f'Behavior spike detected: {today_count} behaviors today vs {avg_daily:.1f} daily average',
                    'severity': 'high'
                })
        
        # Check for critical behaviors today
        if today_critical > 0:
            critical_alerts.append({
                'type': 'critical',
                'message': f'{today_critical} critical behavior(s) recorded today',
                'severity': 'critical'
            })
        
        # Check for intervention effectiveness decline
        if intervention_success_rate < 50 and total_interventions >= 5:
            critical_alerts.append({
                'type': 'intervention',
                'message': f'Low intervention success rate: {intervention_success_rate:.1f}%',
                'severity': 'medium'
            })
        
        return Response({
            'current_stats': {
                'today_total': today_count,
                'today_critical': today_critical,
                'week_total': this_week_count,
                'week_trend_percentage': round(week_trend, 1),
                'week_trend_direction': 'up' if week_trend > 0 else 'down' if week_trend < 0 else 'stable',
                'intervention_success_rate': round(intervention_success_rate, 1)
            },
            'daily_breakdown': daily_data,
            'type_trends': type_trends,
            'severity_distribution': severity_stats,
            'hourly_patterns': hourly_patterns,
            'critical_alerts': critical_alerts,
            'period': {
                'start_date': start_date,
                'end_date': today,
                'days': days_back
            }
        })