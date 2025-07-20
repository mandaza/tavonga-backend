from django.contrib import admin
from .models import Client, Contact, ClientDocument

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = [
        'client_id', 'get_full_name', 'age', 'gender', 'care_level',
        'primary_support_worker', 'is_active', 'created_at'
    ]
    list_filter = [
        'gender', 'care_level', 'is_active', 'primary_support_worker',
        'case_manager', 'created_at'
    ]
    search_fields = [
        'client_id', 'first_name', 'last_name', 'diagnosis', 'interests'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at', 'age']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'client_id', 'first_name', 'middle_name', 'last_name',
                'preferred_name', 'date_of_birth', 'age', 'gender'
            )
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'email')
        }),
        ('Medical & Care Information', {
            'fields': (
                'diagnosis', 'secondary_diagnoses', 'allergies',
                'medications', 'medical_notes', 'care_level'
            )
        }),
        ('Personal Preferences', {
            'fields': (
                'interests', 'likes', 'dislikes', 'communication_preferences',
                'behavioral_triggers', 'calming_strategies'
            )
        }),
        ('Media', {
            'fields': ('profile_picture', 'additional_photos')
        }),
        ('Staff Assignments', {
            'fields': ('primary_support_worker', 'support_team', 'case_manager')
        }),
        ('Administrative', {
            'fields': ('notes', 'is_active')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    filter_horizontal = ['support_team']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'last_name'


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = [
        'get_full_name', 'contact_type', 'relationship', 'client',
        'is_primary_contact', 'phone_primary', 'email', 'is_active'
    ]
    list_filter = [
        'contact_type', 'relationship', 'is_primary_contact',
        'is_active', 'can_pick_up', 'can_receive_updates'
    ]
    search_fields = [
        'first_name', 'last_name', 'phone_primary', 'email',
        'practice_name', 'client__first_name', 'client__last_name'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'client', 'contact_type', 'first_name', 'last_name',
                'relationship', 'relationship_description'
            )
        }),
        ('Contact Information', {
            'fields': (
                'phone_primary', 'phone_secondary', 'email', 'address'
            )
        }),
        ('Professional Information', {
            'fields': ('practice_name', 'specialty', 'license_number'),
            'classes': ('collapse',)
        }),
        ('Preferences & Permissions', {
            'fields': (
                'is_primary_contact', 'can_pick_up', 'can_receive_updates',
                'emergency_only', 'preferred_contact_method'
            )
        }),
        ('Additional Information', {
            'fields': ('notes', 'is_active')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'last_name'


@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'document_type', 'client', 'document_date',
        'is_confidential', 'uploaded_by', 'created_at'
    ]
    list_filter = [
        'document_type', 'is_confidential', 'uploaded_by',
        'document_date', 'created_at'
    ]
    search_fields = [
        'title', 'description', 'client__first_name', 'client__last_name'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Document Information', {
            'fields': (
                'client', 'document_type', 'title', 'description',
                'document_date', 'expiry_date'
            )
        }),
        ('File Information', {
            'fields': ('file_url', 'file_size', 'mime_type')
        }),
        ('Access Control', {
            'fields': (
                'is_confidential', 'access_restricted_to', 'uploaded_by'
            )
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    filter_horizontal = ['access_restricted_to']
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new document
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


# Inline admin for related models
class ContactInline(admin.TabularInline):
    model = Contact
    extra = 1
    fields = [
        'contact_type', 'first_name', 'last_name', 'relationship',
        'phone_primary', 'email', 'is_primary_contact', 'is_active'
    ]
    readonly_fields = ['created_at']


class ClientDocumentInline(admin.TabularInline):
    model = ClientDocument
    extra = 0
    fields = [
        'document_type', 'title', 'document_date', 'file_url',
        'is_confidential'
    ]
    readonly_fields = ['created_at']


# Update ClientAdmin to include inlines
ClientAdmin.inlines = [ContactInline, ClientDocumentInline]
