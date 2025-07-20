from django.contrib import admin
from .models import BehaviorLog

@admin.register(BehaviorLog)
class BehaviorLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'time', 'behavior_type', 'severity', 'location', 'duration_minutes', 'is_critical', 'created_at')
    list_filter = ('behavior_type', 'severity', 'location', 'date', 'harm_to_self', 'harm_to_others', 'property_damage')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specific_location', 'intervention_used', 'notes')
    ordering = ('-date', '-time')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'date', 'time')
        }),
        ('Location & Context', {
            'fields': ('location', 'specific_location', 'activity_before')
        }),
        ('Behavior Details', {
            'fields': ('behavior_type', 'behaviors', 'warning_signs', 'duration_minutes', 'severity')
        }),
        ('Impact Assessment', {
            'fields': ('harm_to_self', 'harm_to_others', 'property_damage', 'damage_description')
        }),
        ('Intervention', {
            'fields': ('intervention_used', 'intervention_effective', 'intervention_notes')
        }),
        ('Follow-up', {
            'fields': ('follow_up_required', 'follow_up_notes')
        }),
        ('Media', {
            'fields': ('photos', 'videos')
        }),
        ('Additional Notes', {
            'fields': ('notes', 'triggers_identified')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def is_critical(self, obj):
        return obj.is_critical
    is_critical.boolean = True
    is_critical.short_description = 'Critical'
