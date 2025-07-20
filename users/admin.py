from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_admin', 'approved', 'is_active_carer', 'created_at')
    list_filter = ('is_admin', 'approved', 'is_active_carer', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Care Management', {
            'fields': ('is_admin', 'approved', 'is_active_carer', 'phone', 'address', 
                      'emergency_contact', 'emergency_phone', 'profile_image', 
                      'date_of_birth', 'hire_date')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Care Management', {
            'fields': ('is_admin', 'approved', 'is_active_carer', 'phone', 'address', 
                      'emergency_contact', 'emergency_phone', 'profile_image', 
                      'date_of_birth', 'hire_date')
        }),
    )
