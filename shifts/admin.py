from django.contrib import admin
from .models import Shift

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('carer', 'date', 'shift_type', 'start_time', 'end_time', 'status', 'clock_in', 'clock_out', 'is_late', 'is_early_leave')
    list_filter = ('status', 'shift_type', 'date', 'assigned_by')
    search_fields = ('carer__username', 'carer__first_name', 'carer__last_name', 'location', 'client_name', 'notes')
    ordering = ('-date', 'start_time')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('carer', 'date', 'shift_type', 'start_time', 'end_time', 'break_duration')
        }),
        ('Clock In/Out', {
            'fields': ('clock_in', 'clock_out', 'clock_in_location', 'clock_out_location')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'assigned_by')
        }),
        ('Location & Client', {
            'fields': ('location', 'client_name', 'client_address')
        }),
        ('Instructions', {
            'fields': ('notes', 'special_instructions', 'emergency_contact')
        }),
        ('Performance', {
            'fields': ('performance_rating', 'supervisor_notes')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('carer', 'assigned_by')
    
    def is_late(self, obj):
        return obj.is_late
    is_late.boolean = True
    is_late.short_description = 'Late'
    
    def is_early_leave(self, obj):
        return obj.is_early_leave
    is_early_leave.boolean = True
    is_early_leave.short_description = 'Early Leave'
