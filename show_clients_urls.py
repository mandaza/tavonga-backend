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

from django.urls import reverse
from rest_framework.routers import DefaultRouter
from clients.views import ClientViewSet, ContactViewSet, ClientDocumentViewSet

def show_clients_urls():
    """Display all available URLs for the clients app"""
    
    print("Clients App API Endpoints:")
    print("=" * 50)
    
    # Create router to get URL patterns
    router = DefaultRouter()
    router.register(r'clients', ClientViewSet)
    router.register(r'contacts', ContactViewSet)
    router.register(r'documents', ClientDocumentViewSet)
    
    print("Base URL: /api/v1/clients/")
    print()
    
    # Client endpoints
    print("📁 CLIENT ENDPOINTS:")
    print("  GET    /api/v1/clients/clients/              - List all clients")
    print("  POST   /api/v1/clients/clients/              - Create new client")
    print("  GET    /api/v1/clients/clients/{id}/         - Get client details")
    print("  PUT    /api/v1/clients/clients/{id}/         - Update client")
    print("  PATCH  /api/v1/clients/clients/{id}/         - Partial update client")
    print("  DELETE /api/v1/clients/clients/{id}/         - Delete client")
    print()
    
    # Client custom actions
    print("📁 CLIENT CUSTOM ACTIONS:")
    print("  GET    /api/v1/clients/clients/summary/                    - Get client summary")
    print("  GET    /api/v1/clients/clients/{id}/contacts/              - Get client contacts")
    print("  GET    /api/v1/clients/clients/{id}/emergency_contacts/    - Get emergency contacts")
    print("  GET    /api/v1/clients/clients/{id}/documents/             - Get client documents")
    print("  GET    /api/v1/clients/clients/by_support_worker/          - Get clients by support worker")
    print("  GET    /api/v1/clients/clients/by_case_manager/            - Get clients by case manager")
    print("  GET    /api/v1/clients/clients/statistics/                 - Get client statistics")
    print()
    
    # Contact endpoints
    print("📞 CONTACT ENDPOINTS:")
    print("  GET    /api/v1/clients/contacts/              - List all contacts")
    print("  POST   /api/v1/clients/contacts/              - Create new contact")
    print("  GET    /api/v1/clients/contacts/{id}/         - Get contact details")
    print("  PUT    /api/v1/clients/contacts/{id}/         - Update contact")
    print("  PATCH  /api/v1/clients/contacts/{id}/         - Partial update contact")
    print("  DELETE /api/v1/clients/contacts/{id}/         - Delete contact")
    print()
    
    # Contact custom actions
    print("📞 CONTACT CUSTOM ACTIONS:")
    print("  GET    /api/v1/clients/contacts/by_type/?type={type}      - Get contacts by type")
    print("  GET    /api/v1/clients/contacts/emergency/                - Get all emergency contacts")
    print()
    
    # Document endpoints
    print("📄 DOCUMENT ENDPOINTS:")
    print("  GET    /api/v1/clients/documents/              - List all documents")
    print("  POST   /api/v1/clients/documents/              - Create new document")
    print("  GET    /api/v1/clients/documents/{id}/         - Get document details")
    print("  PUT    /api/v1/clients/documents/{id}/         - Update document")
    print("  PATCH  /api/v1/clients/documents/{id}/         - Partial update document")
    print("  DELETE /api/v1/clients/documents/{id}/         - Delete document")
    print()
    
    # Document custom actions
    print("📄 DOCUMENT CUSTOM ACTIONS:")
    print("  GET    /api/v1/clients/documents/by_type/?type={type}     - Get documents by type")
    print("  GET    /api/v1/clients/documents/expiring_soon/           - Get expiring documents")
    print()
    
    print("AVAILABLE FILTER PARAMETERS:")
    print("=" * 50)
    print("📁 Clients:")
    print("  - gender: male, female, other, prefer_not_to_say")
    print("  - care_level: low, medium, high, critical")
    print("  - is_active: true, false")
    print("  - primary_support_worker: {user_id}")
    print("  - case_manager: {user_id}")
    print("  - search: first_name, last_name, client_id, diagnosis, interests")
    print("  - ordering: last_name, first_name, date_of_birth, created_at, care_level")
    print()
    
    print("📞 Contacts:")
    print("  - client: {client_id}")
    print("  - contact_type: emergency, family, guardian, gp, specialist, therapist, social_worker, advocate, friend, other")
    print("  - relationship: parent, sibling, guardian, grandparent, aunt_uncle, cousin, friend, doctor, therapist, social_worker, advocate, other")
    print("  - is_primary_contact: true, false")
    print("  - is_active: true, false")
    print("  - search: first_name, last_name, phone_primary, email, practice_name")
    print("  - ordering: contact_type, last_name, first_name, created_at")
    print()
    
    print("📄 Documents:")
    print("  - client: {client_id}")
    print("  - document_type: medical_report, assessment, care_plan, behavior_plan, consent_form, insurance, legal, photo_id, other")
    print("  - is_confidential: true, false")
    print("  - uploaded_by: {user_id}")
    print("  - search: title, description")
    print("  - ordering: document_date, created_at, title")
    print()
    
    print("EXAMPLE USAGE:")
    print("=" * 50)
    print("# Get all active clients with medium care level")
    print("GET /api/v1/clients/clients/?is_active=true&care_level=medium")
    print()
    print("# Search for clients by name")
    print("GET /api/v1/clients/clients/?search=Tavonga")
    print()
    print("# Get emergency contacts for a specific client")
    print("GET /api/v1/clients/clients/{client_id}/emergency_contacts/")
    print()
    print("# Get all care plan documents")
    print("GET /api/v1/clients/documents/?document_type=care_plan")
    print()
    print("# Get documents expiring soon")
    print("GET /api/v1/clients/documents/expiring_soon/")

if __name__ == '__main__':
    show_clients_urls() 