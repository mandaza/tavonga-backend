from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Goal(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic information
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True, null=True)
    
    # Goal details
    target_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Assignment
    assigned_carers = models.ManyToManyField(User, related_name='assigned_goals', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_goals')
    
    # Progress tracking
    progress_percentage = models.IntegerField(default=0, help_text="Progress percentage (0-100)")
    notes = models.TextField(blank=True, null=True)
    
    # Goal completion criteria
    required_activities_count = models.IntegerField(default=0, help_text="Number of activities required to complete this goal")
    completion_threshold = models.IntegerField(default=80, help_text="Percentage threshold to mark goal as completed")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'goals'
        verbose_name = 'Goal'
        verbose_name_plural = 'Goals'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def is_overdue(self):
        if self.target_date and self.status == 'active':
            from django.utils import timezone
            return self.target_date < timezone.now().date()
        return False
    
    @property
    def all_activities(self):
        """Get all activities associated with this goal"""
        activities = []
        activities.extend(self.primary_activities.all())
        activities.extend(self.related_activities.all())
        return list(set(activities))  # Remove duplicates
    
    @property
    def completed_activities_count(self):
        """Count completed activities for this goal"""
        from activities.models import ActivityLog
        activity_ids = [activity.id for activity in self.all_activities]
        return ActivityLog.objects.filter(
            activity_id__in=activity_ids,
            completed=True
        ).count()
    
    @property
    def total_activities_count(self):
        """Count total activities for this goal"""
        return len(self.all_activities)
    
    @property
    def calculated_progress(self):
        """Calculate progress based on completed activities"""
        if self.total_activities_count == 0:
            return 0
        
        # Calculate weighted progress based on activity completion and contribution weights
        total_weight = 0
        completed_weight = 0
        
        for activity in self.all_activities:
            total_weight += activity.goal_contribution_weight
            if activity.logs.filter(completed=True).exists():
                completed_weight += activity.goal_contribution_weight
        
        if total_weight == 0:
            return 0
        
        return int((completed_weight / total_weight) * 100)
    
    def update_progress(self):
        """Update progress percentage based on activity completion"""
        self.progress_percentage = self.calculated_progress
        
        # Auto-complete goal if threshold is met
        if self.progress_percentage >= self.completion_threshold and self.status == 'active':
            self.status = 'completed'
        
        self.save()
    
    @property
    def recent_activity_logs(self):
        """Get recent activity logs for this goal"""
        from activities.models import ActivityLog
        from django.utils import timezone
        from datetime import timedelta
        
        activity_ids = [activity.id for activity in self.all_activities]
        week_ago = timezone.now() - timedelta(days=7)
        
        return ActivityLog.objects.filter(
            activity_id__in=activity_ids,
            created_at__gte=week_ago
        ).order_by('-created_at')
