from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Shift(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    SHIFT_TYPE_CHOICES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('night', 'Night'),
        ('full_day', 'Full Day'),
        ('custom', 'Custom'),
    ]
    
    # Basic information
    carer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shifts')
    date = models.DateField()
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPE_CHOICES, default='custom')
    
    # Time details
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration = models.IntegerField(default=0, help_text="Break duration in minutes")
    
    # Clock in/out tracking
    clock_in = models.DateTimeField(blank=True, null=True)
    clock_out = models.DateTimeField(blank=True, null=True)
    clock_in_location = models.CharField(max_length=200, blank=True, null=True)
    clock_out_location = models.CharField(max_length=200, blank=True, null=True)
    
    # Status and assignment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_shifts')
    
    # Location and client details
    location = models.CharField(max_length=200, blank=True, null=True)
    client_name = models.CharField(max_length=200, blank=True, null=True)
    client_address = models.TextField(blank=True, null=True)
    
    # Notes and special instructions
    notes = models.TextField(blank=True, null=True)
    special_instructions = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=200, blank=True, null=True)
    
    # Performance tracking
    performance_rating = models.IntegerField(blank=True, null=True, help_text="1-5 scale")
    supervisor_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shifts'
        verbose_name = 'Shift'
        verbose_name_plural = 'Shifts'
        ordering = ['-date', 'start_time']
        unique_together = ['carer', 'date', 'start_time']
    
    def __str__(self):
        return f"{self.carer.get_full_name()} - {self.date} ({self.start_time}-{self.end_time})"
    
    @property
    def duration_hours(self):
        """Calculate shift duration in hours"""
        if self.clock_in and self.clock_out:
            duration = self.clock_out - self.clock_in
            return round(duration.total_seconds() / 3600, 2)
        return None
    
    @property
    def is_late(self):
        """Check if carer was late for shift"""
        if self.clock_in and self.start_time:
            from django.utils import timezone
            scheduled_datetime = timezone.make_aware(
                timezone.datetime.combine(self.date, self.start_time)
            )
            return self.clock_in > scheduled_datetime
        return False
    
    @property
    def is_early_leave(self):
        """Check if carer left early"""
        if self.clock_out and self.end_time:
            from django.utils import timezone
            scheduled_end = timezone.make_aware(
                timezone.datetime.combine(self.date, self.end_time)
            )
            return self.clock_out < scheduled_end
        return False
    
    @property
    def is_current_shift(self):
        """Check if this is the current active shift"""
        if self.status == 'in_progress' and self.clock_in and not self.clock_out:
            from django.utils import timezone
            now = timezone.now()
            return self.clock_in.date() == now.date()
        return False
    
    @property
    def is_overdue(self):
        """Check if shift is overdue (scheduled but not started)"""
        if self.status == 'scheduled':
            from django.utils import timezone
            now = timezone.now()
            scheduled_datetime = timezone.make_aware(
                timezone.datetime.combine(self.date, self.start_time)
            )
            return now > scheduled_datetime
        return False
