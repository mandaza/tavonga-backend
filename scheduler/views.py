from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Schedule, ScheduleTemplate, ScheduleReminder, ScheduleConflict
from .serializers import (
    ScheduleListSerializer, ScheduleDetailSerializer, ScheduleCreateSerializer,
    ScheduleUpdateSerializer, ScheduleTemplateSerializer, ScheduleTemplateCreateSerializer,
    ScheduleConflictSerializer, ScheduleReminderSerializer, ScheduleQuickActionSerializer,
    ScheduleRescheduleSerializer
)


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "is_admin", False)


class ScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing schedules with comprehensive scheduling features
    """
    queryset = Schedule.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'priority', 'scheduled_date', 'assigned_user', 'activity', 'completed']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ScheduleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ScheduleUpdateSerializer
        elif self.action == 'list':
            return ScheduleListSerializer
        elif self.action in ['quick_action']:
            return ScheduleQuickActionSerializer
        elif self.action in ['reschedule']:
            return ScheduleRescheduleSerializer
        return ScheduleDetailSerializer
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Schedule.objects.none()
        
        queryset = Schedule.objects.select_related('activity', 'assigned_user', 'created_by')
        
        # Admins can see all schedules, users can only see their own
        if not self.request.user.is_admin:
            queryset = queryset.filter(assigned_user=self.request.user)
        
        return queryset.order_by('scheduled_date', 'scheduled_time')
    
    def get_permissions(self):
        # Only admins can create schedules for other users
        if self.action in ['create'] and self.request.data.get('assigned_user') != str(self.request.user.id):
            return [IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's schedules"""
        today = timezone.now().date()
        schedules = self.get_queryset().filter(scheduled_date=today)
        serializer = ScheduleListSerializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming schedules (next 7 days)"""
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        schedules = self.get_queryset().filter(
            scheduled_date__gte=today,
            scheduled_date__lte=next_week,
            status__in=['scheduled']
        )
        serializer = ScheduleListSerializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue schedules"""
        schedules = self.get_queryset().filter(status='scheduled')
        overdue_schedules = [schedule for schedule in schedules if schedule.is_overdue]
        serializer = ScheduleListSerializer(overdue_schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Get calendar view of schedules for a date range"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedules = self.get_queryset().filter(
            scheduled_date__gte=start_date,
            scheduled_date__lte=end_date
        )
        
        # Group by date
        calendar_data = {}
        for schedule in schedules:
            date_str = schedule.scheduled_date.strftime('%Y-%m-%d')
            if date_str not in calendar_data:
                calendar_data[date_str] = []
            calendar_data[date_str].append(ScheduleListSerializer(schedule).data)
        
        return Response(calendar_data)
    
    @action(detail=True, methods=['post'])
    def quick_action(self, request, pk=None):
        """Perform quick actions on schedules (start, complete, cancel)"""
        schedule = self.get_object()
        serializer = ScheduleQuickActionSerializer(data=request.data)
        
        if serializer.is_valid():
            action_type = serializer.validated_data['action']
            
            if action_type == 'start':
                if schedule.status != 'scheduled':
                    return Response(
                        {'error': 'Can only start scheduled activities'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                schedule.mark_started()
                
            elif action_type == 'complete':
                if schedule.status not in ['scheduled', 'in_progress']:
                    return Response(
                        {'error': 'Can only complete scheduled or in-progress activities'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                completion_percentage = serializer.validated_data.get('completion_percentage', 100)
                completion_notes = serializer.validated_data.get('completion_notes', '')
                schedule.mark_completed(completion_percentage, completion_notes)
                
                # Update ratings if provided
                if serializer.validated_data.get('difficulty_rating'):
                    schedule.difficulty_rating = serializer.validated_data['difficulty_rating']
                if serializer.validated_data.get('satisfaction_rating'):
                    schedule.satisfaction_rating = serializer.validated_data['satisfaction_rating']
                schedule.save()
                
            elif action_type == 'cancel':
                if schedule.status not in ['scheduled', 'in_progress']:
                    return Response(
                        {'error': 'Can only cancel scheduled or in-progress activities'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                reason = serializer.validated_data.get('cancel_reason', '')
                schedule.cancel(reason)
            
            return Response(ScheduleDetailSerializer(schedule).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule an activity to a new date and time"""
        schedule = self.get_object()
        serializer = ScheduleRescheduleSerializer(data=request.data)
        
        if serializer.is_valid():
            new_date = serializer.validated_data['new_date']
            new_time = serializer.validated_data['new_time']
            reason = serializer.validated_data.get('reason', '')
            
            if schedule.status not in ['scheduled']:
                return Response(
                    {'error': 'Can only reschedule scheduled activities'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check for conflicts
            new_datetime = timezone.make_aware(datetime.combine(new_date, new_time))
            duration = schedule.estimated_duration or 60
            new_end = new_datetime + timedelta(minutes=duration)
            
            # Check if user already has a schedule at the new time
            conflicting_schedules = Schedule.objects.filter(
                assigned_user=schedule.assigned_user,
                scheduled_date=new_date,
                status__in=['scheduled', 'in_progress']
            ).exclude(id=schedule.id)
            
            for conflict_schedule in conflicting_schedules:
                conflict_datetime = conflict_schedule.scheduled_datetime
                conflict_duration = conflict_schedule.estimated_duration or 60
                conflict_end = conflict_datetime + timedelta(minutes=conflict_duration)
                
                if (new_datetime < conflict_end and new_end > conflict_datetime):
                    return Response(
                        {'error': f'Time conflict with existing schedule: {conflict_schedule.activity.name} at {conflict_schedule.scheduled_time}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create new schedule
            new_schedule = schedule.reschedule(new_date, new_time)
            
            return Response({
                'message': 'Schedule rescheduled successfully',
                'old_schedule': ScheduleDetailSerializer(schedule).data,
                'new_schedule': ScheduleDetailSerializer(new_schedule).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def conflicts(self, request):
        """Get scheduling conflicts"""
        conflicts = ScheduleConflict.objects.filter(
            resolved=False,
            schedule1__assigned_user=request.user
        ) if not request.user.is_admin else ScheduleConflict.objects.filter(resolved=False)
        
        serializer = ScheduleConflictSerializer(conflicts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get scheduling statistics"""
        queryset = self.get_queryset()
        today = timezone.now().date()
        
        stats = {
            'total_schedules': queryset.count(),
            'scheduled_today': queryset.filter(scheduled_date=today, status='scheduled').count(),
            'in_progress_today': queryset.filter(scheduled_date=today, status='in_progress').count(),
            'completed_today': queryset.filter(scheduled_date=today, status='completed').count(),
            'overdue': len([s for s in queryset.filter(status='scheduled') if s.is_overdue]),
            'upcoming_week': queryset.filter(
                scheduled_date__gte=today,
                scheduled_date__lte=today + timedelta(days=7),
                status='scheduled'
            ).count(),
            'completion_rate': 0
        }
        
        # Calculate completion rate
        total_completed_or_cancelled = queryset.filter(
            status__in=['completed', 'cancelled']
        ).count()
        if stats['total_schedules'] > 0:
            stats['completion_rate'] = round(
                (total_completed_or_cancelled / stats['total_schedules']) * 100, 2
            )
        
        return Response(stats)


class ScheduleTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing schedule templates
    """
    queryset = ScheduleTemplate.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['activity', 'created_by']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ScheduleTemplateCreateSerializer
        return ScheduleTemplateSerializer
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return ScheduleTemplate.objects.none()
        
        queryset = ScheduleTemplate.objects.select_related('activity', 'created_by')
        
        # Users can see their own templates and public ones
        if not self.request.user.is_admin:
            queryset = queryset.filter(created_by=self.request.user)
        
        return queryset.order_by('name')
    
    @action(detail=True, methods=['post'])
    def create_schedule(self, request, pk=None):
        """Create a schedule from a template"""
        template = self.get_object()
        
        # Required fields for creating schedule from template
        scheduled_date = request.data.get('scheduled_date')
        scheduled_time = request.data.get('scheduled_time')
        assigned_user = request.data.get('assigned_user', request.user.id)
        
        if not scheduled_date or not scheduled_time:
            return Response(
                {'error': 'scheduled_date and scheduled_time are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create schedule data from template
        schedule_data = {
            'activity': template.activity.id,
            'assigned_user': assigned_user,
            'scheduled_date': scheduled_date,
            'scheduled_time': scheduled_time,
            'estimated_duration': template.default_duration,
            'priority': template.default_priority,
            'location': template.default_location,
            'preparation_notes': template.default_preparation_notes,
            'reminder_minutes_before': template.default_reminder_minutes,
        }
        
        # Use the schedule create serializer to create the schedule
        serializer = ScheduleCreateSerializer(data=schedule_data, context={'request': request})
        if serializer.is_valid():
            schedule = serializer.save()
            return Response(ScheduleDetailSerializer(schedule).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScheduleReminderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing schedule reminders (read-only)
    """
    queryset = ScheduleReminder.objects.all()
    serializer_class = ScheduleReminderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['schedule', 'reminder_type', 'delivered', 'opened']
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return ScheduleReminder.objects.none()
        
        queryset = ScheduleReminder.objects.select_related('schedule')
        
        # Users can only see reminders for their own schedules
        if not self.request.user.is_admin:
            queryset = queryset.filter(schedule__assigned_user=self.request.user)
        
        return queryset.order_by('-sent_at')


class ScheduleConflictViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing and resolving schedule conflicts
    """
    queryset = ScheduleConflict.objects.all()
    serializer_class = ScheduleConflictSerializer
    permission_classes = [IsAdminUser]  # Only admins can manage conflicts
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['conflict_type', 'resolved']
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return ScheduleConflict.objects.none()
        
        return ScheduleConflict.objects.select_related(
            'schedule1', 'schedule2'
        ).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark a conflict as resolved"""
        conflict = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        
        conflict.resolved = True
        conflict.resolution_notes = resolution_notes
        conflict.resolved_at = timezone.now()
        conflict.save()
        
        return Response(ScheduleConflictSerializer(conflict).data)
