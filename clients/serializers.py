from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Client, Contact, ClientDocument

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for client references"""
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']


class ContactSerializer(serializers.ModelSerializer):
    """Full serializer for Contact model"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    contact_type_display = serializers.CharField(source='get_contact_type_display', read_only=True)
    relationship_display = serializers.CharField(source='get_relationship_display', read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'contact_type', 'contact_type_display', 'first_name', 'last_name', 'full_name',
            'relationship', 'relationship_display', 'relationship_description',
            'phone_primary', 'phone_secondary', 'email', 'address',
            'practice_name', 'specialty', 'license_number',
            'is_primary_contact', 'can_pick_up', 'can_receive_updates', 'emergency_only',
            'preferred_contact_method', 'notes', 'is_active',
            'created_at', 'updated_at'
        ]


class ContactCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating contacts"""
    
    class Meta:
        model = Contact
        fields = [
            'client', 'contact_type', 'first_name', 'last_name', 'relationship',
            'relationship_description', 'phone_primary', 'phone_secondary', 'email', 'address',
            'practice_name', 'specialty', 'license_number', 'is_primary_contact',
            'can_pick_up', 'can_receive_updates', 'emergency_only',
            'preferred_contact_method', 'notes', 'is_active'
        ]


class ContactUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating contacts"""
    
    class Meta:
        model = Contact
        fields = [
            'contact_type', 'first_name', 'last_name', 'relationship',
            'relationship_description', 'phone_primary', 'phone_secondary', 'email', 'address',
            'practice_name', 'specialty', 'license_number', 'is_primary_contact',
            'can_pick_up', 'can_receive_updates', 'emergency_only',
            'preferred_contact_method', 'notes', 'is_active'
        ]


class ClientDocumentSerializer(serializers.ModelSerializer):
    """Full serializer for ClientDocument model"""
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    uploaded_by = UserBasicSerializer(read_only=True)
    access_restricted_to = UserBasicSerializer(many=True, read_only=True)
    
    class Meta:
        model = ClientDocument
        fields = [
            'id', 'document_type', 'document_type_display', 'title', 'description',
            'file_url', 'file_size', 'mime_type', 'document_date', 'expiry_date',
            'uploaded_by', 'is_confidential', 'access_restricted_to',
            'created_at', 'updated_at'
        ]


class ClientDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating client documents"""
    
    class Meta:
        model = ClientDocument
        fields = [
            'client', 'document_type', 'title', 'description', 'file_url',
            'file_size', 'mime_type', 'document_date', 'expiry_date',
            'is_confidential', 'access_restricted_to'
        ]


class ClientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for client lists"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    age = serializers.IntegerField(read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    care_level_display = serializers.CharField(source='get_care_level_display', read_only=True)
    primary_support_worker = UserBasicSerializer(read_only=True)
    contacts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            'id', 'client_id', 'first_name', 'last_name', 'full_name', 'display_name',
            'preferred_name', 'date_of_birth', 'age', 'gender', 'gender_display',
            'care_level', 'care_level_display', 'diagnosis', 'profile_picture',
            'primary_support_worker', 'is_active', 'contacts_count',
            'created_at', 'updated_at'
        ]
    
    def get_contacts_count(self, obj):
        return obj.contacts.filter(is_active=True).count()


class ClientDetailSerializer(serializers.ModelSerializer):
    """Full serializer for client details"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    age = serializers.IntegerField(read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    care_level_display = serializers.CharField(source='get_care_level_display', read_only=True)
    
    # Related objects
    primary_support_worker = UserBasicSerializer(read_only=True)
    support_team = UserBasicSerializer(many=True, read_only=True)
    case_manager = UserBasicSerializer(read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    documents = ClientDocumentSerializer(many=True, read_only=True)
    
    # Statistics
    emergency_contacts = serializers.SerializerMethodField()
    active_contacts_count = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            # Basic info
            'id', 'client_id', 'first_name', 'middle_name', 'last_name', 'full_name',
            'display_name', 'preferred_name', 'date_of_birth', 'age', 'gender',
            'gender_display', 'address', 'phone', 'email',
            
            # Medical & care
            'diagnosis', 'secondary_diagnoses', 'allergies', 'medications', 'medical_notes',
            'care_level', 'care_level_display',
            
            # Personal preferences
            'interests', 'likes', 'dislikes', 'communication_preferences',
            'behavioral_triggers', 'calming_strategies',
            
            # Media
            'profile_picture', 'additional_photos',
            
            # Administrative
            'notes', 'is_active',
            
            # Staff assignments
            'primary_support_worker', 'support_team', 'case_manager',
            
            # Related data
            'contacts', 'documents',
            
            # Statistics
            'emergency_contacts', 'active_contacts_count', 'documents_count',
            
            # Timestamps
            'created_at', 'updated_at'
        ]
    
    def get_emergency_contacts(self, obj):
        emergency_contacts = obj.contacts.filter(contact_type='emergency', is_active=True)
        return ContactSerializer(emergency_contacts, many=True).data
    
    def get_active_contacts_count(self, obj):
        return obj.contacts.filter(is_active=True).count()
    
    def get_documents_count(self, obj):
        return obj.documents.count()


class ClientCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating clients"""
    
    class Meta:
        model = Client
        fields = [
            'client_id', 'first_name', 'middle_name', 'last_name', 'preferred_name',
            'date_of_birth', 'gender', 'address', 'phone', 'email',
            'diagnosis', 'secondary_diagnoses', 'allergies', 'medications', 'medical_notes',
            'care_level', 'interests', 'likes', 'dislikes', 'communication_preferences',
            'behavioral_triggers', 'calming_strategies', 'profile_picture', 'additional_photos',
            'notes', 'is_active', 'primary_support_worker', 'support_team', 'case_manager'
        ]
    
    def validate_client_id(self, value):
        """Ensure client_id is unique"""
        if Client.objects.filter(client_id=value).exists():
            raise serializers.ValidationError("A client with this ID already exists.")
        return value


class ClientUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating clients"""
    
    class Meta:
        model = Client
        fields = [
            'first_name', 'middle_name', 'last_name', 'preferred_name',
            'date_of_birth', 'gender', 'address', 'phone', 'email',
            'diagnosis', 'secondary_diagnoses', 'allergies', 'medications', 'medical_notes',
            'care_level', 'interests', 'likes', 'dislikes', 'communication_preferences',
            'behavioral_triggers', 'calming_strategies', 'profile_picture', 'additional_photos',
            'notes', 'is_active', 'primary_support_worker', 'support_team', 'case_manager'
        ]


class ClientSummarySerializer(serializers.ModelSerializer):
    """Minimal serializer for client summaries and references"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    display_name = serializers.CharField(source='get_display_name', read_only=True)
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'client_id', 'full_name', 'display_name', 'preferred_name',
            'age', 'profile_picture', 'is_active'
        ] 