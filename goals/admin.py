from django.contrib import admin
from .models import Goal

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'priority', 'target_date', 'progress_percentage', 'created_by', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at', 'target_date')
    search_fields = ('name', 'description', 'category', 'created_by__username', 'created_by__first_name', 'created_by__last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Goal Details', {
            'fields': ('target_date', 'status', 'priority', 'progress_percentage', 'notes')
        }),
        ('Assignment', {
            'fields': ('assigned_carers', 'created_by')
        }),
    )
    
    filter_horizontal = ('assigned_carers',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
