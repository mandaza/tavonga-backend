from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Activity(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    CATEGORY_CHOICES = [
        ('daily_living', 'Daily Living'),
        ('social', 'Social'),
        ('educational', 'Educational'),
        ('recreational', 'Recreational'),
        ('therapeutic', 'Therapeutic'),
        ('other', 'Other'),
    ]
    
    # Basic information
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    
    # Activity details
    instructions = models.TextField(help_text="Step-by-step instructions")
    prerequisites = models.TextField(blank=True, null=True, help_text="Required skills or conditions")
    estimated_duration = models.IntegerField(help_text="Estimated duration in minutes", blank=True, null=True)
    
    # Goal associations - Primary goal (one-to-many)
    primary_goal = models.ForeignKey('goals.Goal', on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_activities')
    
    # Goal associations - Multiple goals (many-to-many)
    related_goals = models.ManyToManyField('goals.Goal', related_name='related_activities', blank=True)
    
    # Goal contribution weight (how much this activity contributes to goal progress)
    goal_contribution_weight = models.IntegerField(default=1, help_text="Weight of this activity's contribution to goal progress (1-10)")
    
    # Media and resources
    image_url = models.URLField(blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_activities')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'activities'
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    @property
    def all_goals(self):
        """Get all goals this activity contributes to"""
        goals = []
        if self.primary_goal:
            goals.append(self.primary_goal)
        goals.extend(self.related_goals.all())
        return list(set(goals))  # Remove duplicates
    
    @property
    def completion_rate(self):
        """Calculate completion rate for this activity"""
        total_logs = self.logs.count()
        if total_logs == 0:
            return 0
        completed_logs = self.logs.filter(completed=True).count()
        return (completed_logs / total_logs) * 100
    
    @property
    def behavior_incident_count(self):
        """Count of behavior incidents related to this activity"""
        return self.behavior_logs.count()
    
    @property
    def behavior_risk_level(self):
        """Calculate risk level based on behavior incidents"""
        behavior_count = self.behavior_incident_count
        if behavior_count == 0:
            return 'low'
        elif behavior_count <= 2:
            return 'medium'
        else:
            return 'high'
    
    @property
    def critical_behavior_count(self):
        """Count of critical behavior incidents related to this activity"""
        return self.behavior_logs.filter(severity='critical').count()
    
    @property
    def behavior_statistics(self):
        """Get comprehensive behavior statistics for this activity"""
        from django.db.models import Count, Q
        
        behavior_logs = self.behavior_logs.all()
        
        if not behavior_logs.exists():
            return {
                'total_incidents': 0,
                'risk_level': 'low',
                'most_common_behavior': None,
                'most_common_occurrence': None,
                'intervention_success_rate': 0
            }
        
        # Count by behavior type
        behavior_types = behavior_logs.values('behavior_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Count by occurrence type
        occurrence_types = behavior_logs.values('behavior_occurrence').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Intervention success rate
        total_with_intervention = behavior_logs.filter(
            intervention_effective__isnull=False
        ).count()
        successful_interventions = behavior_logs.filter(
            intervention_effective=True
        ).count()
        
        success_rate = (successful_interventions / total_with_intervention * 100) if total_with_intervention > 0 else 0
        
        return {
            'total_incidents': behavior_logs.count(),
            'risk_level': self.behavior_risk_level,
            'most_common_behavior': behavior_types.first()['behavior_type'] if behavior_types else None,
            'most_common_occurrence': occurrence_types.first()['behavior_occurrence'] if occurrence_types else None,
            'intervention_success_rate': round(success_rate, 2),
            'critical_incidents': self.critical_behavior_count
        }


class ActivityLog(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('skipped', 'Skipped'),
    ]
    
    # Relationships
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    
    # Log details
    date = models.DateField()
    scheduled_time = models.TimeField(blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Completion details
    completed = models.BooleanField(default=False)
    completion_notes = models.TextField(blank=True, null=True)
    difficulty_rating = models.IntegerField(blank=True, null=True, help_text="1-5 scale")
    satisfaction_rating = models.IntegerField(blank=True, null=True, help_text="1-5 scale")
    
    # Media
    photos = models.JSONField(default=list, blank=True, help_text="List of photo URLs")
    videos = models.JSONField(default=list, blank=True, help_text="List of video URLs")
    
    # Additional notes
    notes = models.TextField(blank=True, null=True)
    challenges = models.TextField(blank=True, null=True)
    successes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'activity_logs'
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        ordering = ['-date', '-created_at']
        unique_together = ['activity', 'user', 'date']
    
    def __str__(self):
        return f"{self.activity.name} - {self.user.get_full_name()} ({self.date})"
    
    @property
    def duration_minutes(self):
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            return int(duration.total_seconds() / 60)
        return None
    
    @property
    def is_overdue(self):
        if self.status == 'scheduled' and self.scheduled_time:
            from django.utils import timezone
            now = timezone.now()
            scheduled_datetime = timezone.make_aware(
                timezone.datetime.combine(self.date, self.scheduled_time)
            )
            return now > scheduled_datetime
        return False
