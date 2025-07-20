from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, date, time
from activities.models import Activity

User = get_user_model()


class Schedule(models.Model):
    """Main schedule model that represents a scheduled activity"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    RECURRENCE_CHOICES = [
        ('none', 'No Recurrence'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    # Core scheduling information
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='schedules')
    assigned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_schedules')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_schedules')
    
    # Schedule timing
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    estimated_duration = models.IntegerField(help_text="Estimated duration in minutes", null=True, blank=True)
    
    # Actual timing (filled when activity starts/ends)
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Recurrence
    recurrence_type = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, default='none')
    recurrence_end_date = models.DateField(null=True, blank=True)
    parent_schedule = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='recurring_schedules')
    
    # Notes and instructions
    notes = models.TextField(blank=True, null=True, help_text="General notes about this scheduled activity")
    preparation_notes = models.TextField(blank=True, null=True, help_text="Notes about preparation needed")
    completion_notes = models.TextField(blank=True, null=True, help_text="Notes after completion")
    
    # Location and setup
    location = models.CharField(max_length=200, blank=True, null=True)
    special_requirements = models.TextField(blank=True, null=True)
    
    # Reminder settings
    send_reminder = models.BooleanField(default=True)
    reminder_minutes_before = models.IntegerField(default=30, help_text="Minutes before scheduled time to send reminder")
    reminder_sent = models.BooleanField(default=False)
    
    # Completion tracking
    completed = models.BooleanField(default=False)
    completion_percentage = models.IntegerField(default=0, help_text="Percentage of activity completed (0-100)")
    difficulty_rating = models.IntegerField(null=True, blank=True, help_text="Difficulty rating from 1-5")
    satisfaction_rating = models.IntegerField(null=True, blank=True, help_text="Satisfaction rating from 1-5")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedules'
        verbose_name = 'Schedule'
        verbose_name_plural = 'Schedules'
        ordering = ['scheduled_date', 'scheduled_time']
        unique_together = ['activity', 'assigned_user', 'scheduled_date', 'scheduled_time']
    
    def __str__(self):
        return f"{self.activity.name} - {self.assigned_user.get_full_name()} ({self.scheduled_date} at {self.scheduled_time})"
    
    @property
    def scheduled_datetime(self):
        """Combine scheduled date and time into datetime"""
        if self.scheduled_date and self.scheduled_time:
            return timezone.make_aware(datetime.combine(self.scheduled_date, self.scheduled_time))
        return None
    
    @property
    def is_overdue(self):
        """Check if the scheduled activity is overdue"""
        if self.status not in ['scheduled'] or not self.scheduled_datetime:
            return False
        now = timezone.now()
        return now > self.scheduled_datetime
    
    @property
    def is_today(self):
        """Check if scheduled for today"""
        if not self.scheduled_date:
            return False
        return self.scheduled_date == timezone.now().date()
    
    @property
    def is_upcoming(self):
        """Check if scheduled for future"""
        if not self.scheduled_date:
            return False
        return self.scheduled_date > timezone.now().date()
    
    @property
    def actual_duration_minutes(self):
        """Calculate actual duration in minutes"""
        if self.actual_start_time and self.actual_end_time:
            duration = self.actual_end_time - self.actual_start_time
            return int(duration.total_seconds() / 60)
        return None
    
    @property
    def time_until_scheduled(self):
        """Get time until scheduled datetime"""
        if self.status != 'scheduled' or not self.scheduled_datetime:
            return None
        now = timezone.now()
        scheduled_dt = self.scheduled_datetime
        if scheduled_dt > now:
            delta = scheduled_dt - now
            return delta
        return None
    
    def mark_started(self):
        """Mark the schedule as started"""
        self.status = 'in_progress'
        self.actual_start_time = timezone.now()
        self.save()
    
    def mark_completed(self, completion_percentage=100, notes=None):
        """Mark the schedule as completed"""
        self.status = 'completed'
        self.completed = True
        self.completion_percentage = completion_percentage
        self.actual_end_time = timezone.now()
        if notes:
            self.completion_notes = notes
        self.save()
    
    def cancel(self, reason=None):
        """Cancel the scheduled activity"""
        self.status = 'cancelled'
        if reason:
            self.completion_notes = f"Cancelled: {reason}"
        self.save()
    
    def reschedule(self, new_date, new_time):
        """Reschedule to a new date and time"""
        self.status = 'rescheduled'
        
        # Create a new schedule with the new timing
        new_schedule = Schedule.objects.create(
            activity=self.activity,
            assigned_user=self.assigned_user,
            created_by=self.created_by,
            scheduled_date=new_date,
            scheduled_time=new_time,
            estimated_duration=self.estimated_duration,
            priority=self.priority,
            notes=self.notes,
            preparation_notes=self.preparation_notes,
            location=self.location,
            special_requirements=self.special_requirements,
            send_reminder=self.send_reminder,
            reminder_minutes_before=self.reminder_minutes_before,
        )
        
        self.save()
        return new_schedule


class ScheduleTemplate(models.Model):
    """Template for creating recurring schedules"""
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    
    # Default scheduling settings
    default_duration = models.IntegerField(help_text="Default duration in minutes")
    default_priority = models.CharField(max_length=10, choices=Schedule.PRIORITY_CHOICES, default='medium')
    default_location = models.CharField(max_length=200, blank=True)
    default_preparation_notes = models.TextField(blank=True)
    
    # Reminder settings
    default_reminder_minutes = models.IntegerField(default=30)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedule_templates'
        verbose_name = 'Schedule Template'
        verbose_name_plural = 'Schedule Templates'
    
    def __str__(self):
        return f"{self.name} - {self.activity.name}"


class ScheduleReminder(models.Model):
    """Track reminders sent for schedules"""
    
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ])
    
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    opened = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'schedule_reminders'
        verbose_name = 'Schedule Reminder'
        verbose_name_plural = 'Schedule Reminders'


class ScheduleConflict(models.Model):
    """Track scheduling conflicts"""
    
    schedule1 = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='conflicts_as_first')
    schedule2 = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='conflicts_as_second')
    conflict_type = models.CharField(max_length=50, choices=[
        ('time_overlap', 'Time Overlap'),
        ('resource_conflict', 'Resource Conflict'),
        ('user_double_booking', 'User Double Booking'),
    ])
    
    resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'schedule_conflicts'
        verbose_name = 'Schedule Conflict'
        verbose_name_plural = 'Schedule Conflicts'
