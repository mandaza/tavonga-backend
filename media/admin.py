from django.contrib import admin
from .models import MediaFile

@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'media_type', 'file', 'uploaded_by', 'created_at')
    list_filter = ('media_type', 'uploaded_by', 'created_at')
    search_fields = ('file', 'description', 'uploaded_by__username')
    ordering = ('-created_at',)
