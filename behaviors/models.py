from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

User = get_user_model()

class BehaviorLog(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    BEHAVIOR_TYPE_CHOICES = [
        ('aggression', 'Aggression'),
        ('self_injury', 'Self-Injury'),
        ('property_damage', 'Property Damage'),
        ('elopement', 'Elopement'),
        ('non_compliance', 'Non-Compliance'),
        ('disruption', 'Disruption'),
        ('other', 'Other'),
    ]
    
    LOCATION_CHOICES = [
        ('home', 'Home'),
        ('school', 'School'),
        ('community', 'Community'),
        ('therapy', 'Therapy'),
        ('transport', 'Transport'),
        ('other', 'Other'),
    ]
    
    BEHAVIOR_OCCURRENCE_CHOICES = [
        ('before_activity', 'Before Activity'),
        ('during_activity', 'During Activity'),
        ('after_activity', 'After Activity'),
        ('unrelated', 'Unrelated to Activity'),
    ]
    
    # Basic information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='behavior_logs')
    date = models.DateField()
    time = models.TimeField()
    
    # Location and context
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='other')
    specific_location = models.CharField(max_length=200, blank=True, null=True, help_text="Specific location details")
    
    # Activity relationships - NEW FIELDS
    related_activity = models.ForeignKey(
        'activities.Activity', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='behavior_logs',
        help_text="Activity associated with this behavior"
    )
    related_activity_log = models.ForeignKey(
        'activities.ActivityLog', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='behavior_logs',
        help_text="Specific activity log instance associated with this behavior"
    )
    behavior_occurrence = models.CharField(
        max_length=20, 
        choices=BEHAVIOR_OCCURRENCE_CHOICES,
        default='unrelated',
        help_text="When the behavior occurred relative to the activity"
    )
    
    # Keep the existing text field for backward compatibility
    activity_before = models.TextField(blank=True, null=True, help_text="What was happening before the behavior")
    
    # Behavior details
    behavior_type = models.CharField(max_length=20, choices=BEHAVIOR_TYPE_CHOICES, default='other')
    behaviors = models.JSONField(default=list, help_text="List of specific behaviors observed")
    warning_signs = models.JSONField(default=list, blank=True, help_text="Warning signs observed before behavior")
    
    # Duration and severity
    duration_minutes = models.IntegerField(blank=True, null=True, help_text="Duration of the behavior in minutes")
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    
    # Impact assessment
    harm_to_self = models.BooleanField(default=False)
    harm_to_others = models.BooleanField(default=False)
    property_damage = models.BooleanField(default=False)
    damage_description = models.TextField(blank=True, null=True)
    
    # Intervention
    intervention_used = models.TextField(help_text="What intervention was used")
    intervention_effective = models.BooleanField(blank=True, null=True, help_text="Was the intervention effective?")
    intervention_notes = models.TextField(blank=True, null=True)
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True, null=True)
    
    # Media attachments
    photos = models.JSONField(default=list, blank=True, help_text="List of photo URLs")
    videos = models.JSONField(default=list, blank=True, help_text="List of video URLs")
    
    # Additional notes
    notes = models.TextField(blank=True, null=True)
    triggers_identified = models.JSONField(default=list, blank=True, help_text="Potential triggers identified")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'behavior_logs'
        verbose_name = 'Behavior Log'
        verbose_name_plural = 'Behavior Logs'
        ordering = ['-date', '-time']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_behavior_type_display()} ({self.date})"
    
    @property
    def is_critical(self):
        return self.severity == 'critical' or self.harm_to_self or self.harm_to_others
    
    @property
    def requires_immediate_attention(self):
        return self.is_critical or self.follow_up_required
    
    @property
    def is_activity_related(self):
        """Check if this behavior is related to any activity"""
        return self.related_activity is not None or self.related_activity_log is not None
    
    @property
    def activity_context(self):
        """Get activity context information"""
        if self.related_activity_log:
            return {
                'activity': self.related_activity_log.activity,
                'activity_log': self.related_activity_log,
                'occurrence': self.get_behavior_occurrence_display()
            }
        elif self.related_activity:
            return {
                'activity': self.related_activity,
                'activity_log': None,
                'occurrence': self.get_behavior_occurrence_display()
            }
        return None
