from django.contrib import admin
from .models import Schedule, ScheduleTemplate, ScheduleReminder, ScheduleConflict


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'activity', 'assigned_user', 'scheduled_date', 'scheduled_time', 
        'status', 'priority', 'completed', 'is_overdue'
    ]
    list_filter = [
        'status', 'priority', 'completed', 'scheduled_date', 
        'recurrence_type', 'send_reminder'
    ]
    search_fields = [
        'activity__name', 'assigned_user__first_name', 
        'assigned_user__last_name', 'notes'
    ]
    readonly_fields = [
        'is_overdue', 'is_today', 'is_upcoming', 'scheduled_datetime',
        'actual_duration_minutes', 'time_until_scheduled', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('activity', 'assigned_user', 'created_by')
        }),
        ('Scheduling', {
            'fields': (
                'scheduled_date', 'scheduled_time', 'estimated_duration',
                'actual_start_time', 'actual_end_time'
            )
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'completed', 'completion_percentage')
        }),
        ('Recurrence', {
            'fields': ('recurrence_type', 'recurrence_end_date', 'parent_schedule'),
            'classes': ('collapse',)
        }),
        ('Location & Requirements', {
            'fields': ('location', 'special_requirements'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'preparation_notes', 'completion_notes'),
            'classes': ('collapse',)
        }),
        ('Reminders', {
            'fields': ('send_reminder', 'reminder_minutes_before', 'reminder_sent'),
            'classes': ('collapse',)
        }),
        ('Ratings', {
            'fields': ('difficulty_rating', 'satisfaction_rating'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': (
                'is_overdue', 'is_today', 'is_upcoming', 'scheduled_datetime',
                'actual_duration_minutes', 'time_until_scheduled', 
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'activity', 'assigned_user', 'created_by', 'parent_schedule'
        )


@admin.register(ScheduleTemplate)
class ScheduleTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'activity', 'default_duration', 'default_priority', 'created_by'
    ]
    list_filter = ['default_priority', 'created_at']
    search_fields = ['name', 'description', 'activity__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'activity', 'created_by')
        }),
        ('Default Settings', {
            'fields': (
                'default_duration', 'default_priority', 'default_location',
                'default_preparation_notes', 'default_reminder_minutes'
            )
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('activity', 'created_by')


@admin.register(ScheduleReminder)
class ScheduleReminderAdmin(admin.ModelAdmin):
    list_display = [
        'schedule', 'reminder_type', 'sent_at', 'delivered', 'opened'
    ]
    list_filter = ['reminder_type', 'delivered', 'opened', 'sent_at']
    search_fields = ['schedule__activity__name', 'schedule__assigned_user__first_name']
    readonly_fields = ['sent_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('schedule')


@admin.register(ScheduleConflict)
class ScheduleConflictAdmin(admin.ModelAdmin):
    list_display = [
        'schedule1', 'schedule2', 'conflict_type', 'resolved', 'created_at'
    ]
    list_filter = ['conflict_type', 'resolved', 'created_at']
    search_fields = [
        'schedule1__activity__name', 'schedule2__activity__name',
        'resolution_notes'
    ]
    readonly_fields = ['created_at', 'resolved_at']
    fieldsets = (
        ('Conflict Information', {
            'fields': ('schedule1', 'schedule2', 'conflict_type')
        }),
        ('Resolution', {
            'fields': ('resolved', 'resolution_notes', 'resolved_at')
        }),
        ('System Info', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'schedule1', 'schedule2'
        )
