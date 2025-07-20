from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# Create your models here.

class User(AbstractUser):
    # Role-based fields
    ROLE_CHOICES = [
        ('support_worker', 'Support Worker'),
        ('practitioner', 'Practitioner'),
        ('family', 'Family'),
        ('super_admin', 'Super Admin'),
    ]
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default='support_worker')
    is_admin = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    
    # Profile information
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)
    emergency_phone = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.URLField(blank=True, null=True)
    
    # Additional fields
    date_of_birth = models.DateField(blank=True, null=True)
    hire_date = models.DateField(blank=True, null=True)
    is_active_carer = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at', 'username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    @property
    def is_carer(self):
        return not self.is_admin
    
    @property
    def full_name(self):
        return self.get_full_name()
