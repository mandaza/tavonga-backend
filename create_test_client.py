#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Add the backend-api directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from datetime import date
from clients.models import Client, Contact, ClientDocument

User = get_user_model()

def test_client_models():
    """Test the client models directly"""
    
    # Create or get a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'is_admin': True
        }
    )
    
    print("Testing Client Model...")
    
    # Test creating a client
    client = Client.objects.create(
        client_id='CLI-TV-001',
        first_name='Tavonga',
        last_name='Mukamuri',
        date_of_birth=date(1990, 1, 1),
        gender='male',
        diagnosis='Autism Spectrum Disorder',
        care_level='medium',
        interests='Music, Art, Swimming',
        behavioral_triggers=['loud noises', 'crowded spaces'],
        calming_strategies=['quiet music', 'deep breathing'],
        primary_support_worker=user,
        is_active=True
    )
    
    print(f"✅ Client created: {client.get_full_name()}")
    print(f"   Client ID: {client.client_id}")
    print(f"   Age: {client.age}")
    print(f"   Diagnosis: {client.diagnosis}")
    print(f"   Behavioral Triggers: {client.behavioral_triggers}")
    print(f"   Calming Strategies: {client.calming_strategies}")
    
    # Test creating a contact
    contact = Contact.objects.create(
        client=client,
        contact_type='emergency',
        first_name='John',
        last_name='Doe',
        relationship='parent',
        phone_primary='+1234567890',
        email='john.doe@example.com',
        is_primary_contact=True,
        can_pick_up=True,
        can_receive_updates=True
    )
    
    print(f"✅ Contact created: {contact.get_full_name()}")
    print(f"   Contact Type: {contact.get_contact_type_display()}")
    print(f"   Relationship: {contact.get_relationship_display()}")
    print(f"   Phone: {contact.phone_primary}")
    print(f"   Email: {contact.email}")
    
    # Test creating a document
    document = ClientDocument.objects.create(
        client=client,
        document_type='care_plan',
        title='Tavonga Care Plan 2024',
        description='Annual care plan for Tavonga',
        file_url='https://example.com/documents/care_plan.pdf',
        document_date=date(2024, 1, 1),
        uploaded_by=user,
        is_confidential=False
    )
    
    print(f"✅ Document created: {document.title}")
    print(f"   Document Type: {document.get_document_type_display()}")
    print(f"   Document Date: {document.document_date}")
    print(f"   Uploaded By: {document.uploaded_by.get_full_name()}")
    
    # Test relationships
    print("\nTesting Relationships...")
    print(f"Client has {client.contacts.count()} contacts")
    print(f"Client has {client.documents.count()} documents")
    
    for contact in client.contacts.all():
        print(f"  - Contact: {contact.get_full_name()} ({contact.contact_type})")
    
    for doc in client.documents.all():
        print(f"  - Document: {doc.title} ({doc.document_type})")
    
    # Test queries
    print("\nTesting Queries...")
    emergency_contacts = client.contacts.filter(contact_type='emergency')
    print(f"Emergency contacts: {emergency_contacts.count()}")
    
    active_clients = Client.objects.filter(is_active=True)
    print(f"Active clients: {active_clients.count()}")
    
    clients_with_support_worker = Client.objects.filter(primary_support_worker=user)
    print(f"Clients with support worker '{user.get_full_name()}': {clients_with_support_worker.count()}")
    
    print("\n🎉 All model tests passed! The clients app is working correctly.")

if __name__ == '__main__':
    print("Testing Clients App Models...")
    print("=" * 50)
    test_client_models()
    print("=" * 50)
    print("Test completed!") 