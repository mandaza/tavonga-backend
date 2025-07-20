from django.contrib import admin
from .models import Activity, ActivityLog

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'difficulty', 'primary_goal', 'is_active', 'created_by', 'created_at')
    list_filter = ('category', 'difficulty', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'instructions', 'created_by__username')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'difficulty')
        }),
        ('Activity Details', {
            'fields': ('instructions', 'prerequisites', 'estimated_duration')
        }),
        ('Goal Association', {
            'fields': ('primary_goal', 'related_goals')
        }),
        ('Media', {
            'fields': ('image_url', 'video_url')
        }),
        ('Status', {
            'fields': ('is_active', 'created_by')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('primary_goal', 'created_by')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('activity', 'user', 'date', 'status', 'completed', 'scheduled_time', 'created_at')
    list_filter = ('status', 'completed', 'date', 'activity__category')
    search_fields = ('activity__name', 'user__username', 'user__first_name', 'user__last_name', 'notes')
    ordering = ('-date', '-created_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('activity', 'user', 'date', 'scheduled_time', 'status')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time')
        }),
        ('Completion', {
            'fields': ('completed', 'completion_notes', 'difficulty_rating', 'satisfaction_rating')
        }),
        ('Media', {
            'fields': ('photos', 'videos')
        }),
        ('Notes', {
            'fields': ('notes', 'challenges', 'successes')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('activity', 'user')
