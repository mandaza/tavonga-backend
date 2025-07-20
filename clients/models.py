from django.db import models
from django.contrib.auth import get_user_model
import uuid
import json

User = get_user_model()

class Client(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    CARE_LEVEL_CHOICES = [
        ('low', 'Low Support'),
        ('medium', 'Medium Support'),
        ('high', 'High Support'),
        ('critical', 'Critical Support'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    preferred_name = models.CharField(max_length=100, blank=True, null=True, help_text="What the client likes to be called")
    
    # Personal Details
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='prefer_not_to_say')
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Medical & Care Information
    diagnosis = models.TextField(help_text="Primary diagnosis and conditions")
    secondary_diagnoses = models.TextField(blank=True, null=True, help_text="Additional diagnoses or conditions")
    allergies = models.TextField(blank=True, null=True, help_text="Known allergies and reactions")
    medications = models.TextField(blank=True, null=True, help_text="Current medications and dosages")
    medical_notes = models.TextField(blank=True, null=True, help_text="Additional medical information")
    care_level = models.CharField(max_length=20, choices=CARE_LEVEL_CHOICES, default='medium')
    
    # Personal Interests & Preferences
    interests = models.TextField(blank=True, null=True, help_text="Client's interests and hobbies")
    likes = models.TextField(blank=True, null=True, help_text="Things the client enjoys")
    dislikes = models.TextField(blank=True, null=True, help_text="Things the client dislikes or finds distressing")
    communication_preferences = models.TextField(blank=True, null=True, help_text="How the client prefers to communicate")
    behavioral_triggers = models.JSONField(
        blank=True,
        default=list,
        help_text="Known behavioral triggers"
    )
    calming_strategies = models.JSONField(
        blank=True,
        default=list,
        help_text="Effective calming strategies"
    )
    
    # Profile & Media
    profile_picture = models.URLField(blank=True, null=True, help_text="URL to profile picture")
    additional_photos = models.JSONField(
        blank=True,
        default=list,
        help_text="Additional photos (family, activities, etc.)"
    )
    
    # Administrative
    client_id = models.CharField(max_length=50, unique=True, help_text="Unique client identifier")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True, help_text="General notes about the client")
    
    # Assigned staff
    primary_support_worker = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='primary_clients',
        help_text="Primary support worker assigned to this client"
    )
    support_team = models.ManyToManyField(
        User,
        blank=True,
        related_name='supported_clients',
        help_text="Support team members working with this client"
    )
    case_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_clients',
        help_text="Case manager responsible for this client"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clients'
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.client_id})"
    
    def get_full_name(self):
        """Return the client's full name"""
        middle = f" {self.middle_name}" if self.middle_name else ""
        return f"{self.first_name}{middle} {self.last_name}"
    
    def get_display_name(self):
        """Return preferred name or full name"""
        return self.preferred_name or self.get_full_name()
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))


class Contact(models.Model):
    CONTACT_TYPE_CHOICES = [
        ('emergency', 'Emergency Contact'),
        ('family', 'Family Member'),
        ('guardian', 'Guardian'),
        ('gp', 'General Practitioner'),
        ('specialist', 'Medical Specialist'),
        ('therapist', 'Therapist'),
        ('social_worker', 'Social Worker'),
        ('advocate', 'Advocate'),
        ('friend', 'Friend'),
        ('other', 'Other'),
    ]
    
    RELATIONSHIP_CHOICES = [
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('guardian', 'Guardian'),
        ('grandparent', 'Grandparent'),
        ('aunt_uncle', 'Aunt/Uncle'),
        ('cousin', 'Cousin'),
        ('friend', 'Friend'),
        ('doctor', 'Doctor'),
        ('therapist', 'Therapist'),
        ('social_worker', 'Social Worker'),
        ('advocate', 'Advocate'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    
    # Contact Details
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, blank=True, null=True)
    relationship_description = models.CharField(max_length=200, blank=True, null=True, help_text="Additional relationship details")
    
    # Contact Information
    phone_primary = models.CharField(max_length=20, blank=True, null=True)
    phone_secondary = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Professional Information (for medical contacts)
    practice_name = models.CharField(max_length=200, blank=True, null=True)
    specialty = models.CharField(max_length=200, blank=True, null=True)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Preferences & Permissions
    is_primary_contact = models.BooleanField(default=False, help_text="Primary contact for this contact type")
    can_pick_up = models.BooleanField(default=False, help_text="Authorized to pick up client")
    can_receive_updates = models.BooleanField(default=True, help_text="Can receive progress updates")
    emergency_only = models.BooleanField(default=False, help_text="Contact only in emergencies")
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[('phone', 'Phone'), ('email', 'Email'), ('text', 'Text Message')],
        default='phone'
    )
    
    # Additional Information
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'client_contacts'
        verbose_name = 'Client Contact'
        verbose_name_plural = 'Client Contacts'
        ordering = ['contact_type', 'last_name', 'first_name']
        unique_together = ['client', 'contact_type', 'is_primary_contact']
    
    def __str__(self):
        contact_type_display = self.get_contact_type_display()
        return f"{self.get_full_name()} - {contact_type_display} for {self.client.get_display_name()}"
    
    def get_full_name(self):
        """Return the contact's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary contact per type per client
        if self.is_primary_contact:
            Contact.objects.filter(
                client=self.client,
                contact_type=self.contact_type,
                is_primary_contact=True
            ).exclude(id=self.id).update(is_primary_contact=False)
        
        super().save(*args, **kwargs)


class ClientDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('medical_report', 'Medical Report'),
        ('assessment', 'Assessment'),
        ('care_plan', 'Care Plan'),
        ('behavior_plan', 'Behavior Support Plan'),
        ('consent_form', 'Consent Form'),
        ('insurance', 'Insurance Information'),
        ('legal', 'Legal Document'),
        ('photo_id', 'Photo ID'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='documents')
    
    # Document Details
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    file_url = models.URLField(help_text="URL to the document file")
    file_size = models.PositiveIntegerField(blank=True, null=True, help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    
    # Document Metadata
    document_date = models.DateField(blank=True, null=True, help_text="Date the document was created/issued")
    expiry_date = models.DateField(blank=True, null=True, help_text="Document expiry date (if applicable)")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_documents')
    
    # Access Control
    is_confidential = models.BooleanField(default=False)
    access_restricted_to = models.ManyToManyField(
        User,
        blank=True,
        related_name='accessible_documents',
        help_text="Users who can access this document (if restricted)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'client_documents'
        verbose_name = 'Client Document'
        verbose_name_plural = 'Client Documents'
        ordering = ['-document_date', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.client.get_display_name()}"
