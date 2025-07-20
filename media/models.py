from django.db import models
from django.contrib.auth import get_user_model
from PIL import Image
import os
from io import BytesIO
from django.core.files.base import ContentFile
from behaviors.models import BehaviorLog
from activities.models import ActivityLog

User = get_user_model()

class MediaFile(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    thumbnail = models.ImageField(upload_to='uploads/thumbnails/%Y/%m/%d/', blank=True, null=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_files')
    description = models.TextField(blank=True)
    behavior_log = models.ForeignKey(BehaviorLog, null=True, blank=True, on_delete=models.CASCADE, related_name='media')
    activity_log = models.ForeignKey(ActivityLog, null=True, blank=True, on_delete=models.CASCADE, related_name='media')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'media_files'
        verbose_name = 'Media File'
        verbose_name_plural = 'Media Files'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.behavior_log:
            return f"{self.media_type}: {self.file.name} (BehaviorLog {self.behavior_log.id})"
        if self.activity_log:
            return f"{self.media_type}: {self.file.name} (ActivityLog {self.activity_log.id})"
        return f"{self.media_type}: {self.file.name} ({self.uploaded_by})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.media_type == 'image' and self.file and not self.thumbnail:
            self.generate_thumbnail()

    def generate_thumbnail(self):
        try:
            img = Image.open(self.file)
            img.thumbnail((300, 300))
            thumb_io = BytesIO()
            img_format = img.format if img.format else 'JPEG'
            img.save(thumb_io, format=img_format)
            thumb_name = os.path.splitext(self.file.name)[0] + '_thumb.jpg'
            self.thumbnail.save(thumb_name, ContentFile(thumb_io.getvalue()), save=False)
            self.save(update_fields=['thumbnail'])
        except Exception as e:
            pass  # Optionally log error
