# Clients App - Tavonga Support System

## Overview
The Clients app manages client/participant information in the Tavonga Support System. It stores comprehensive information about clients including personal details, medical information, contacts, and documents.

## Models

### Client
The main model for storing client information.

**Key Fields:**
- `client_id`: Unique identifier for the client
- `first_name`, `middle_name`, `last_name`: Name information
- `preferred_name`: What the client likes to be called
- `date_of_birth`: Birth date (automatically calculates age)
- `gender`: Gender identity
- `diagnosis`: Primary diagnosis and conditions
- `care_level`: Support level (low, medium, high, critical)
- `interests`: Client's interests and hobbies
- `behavioral_triggers`: Array of known behavioral triggers
- `calming_strategies`: Array of effective calming strategies
- `primary_support_worker`: Assigned primary support worker
- `support_team`: Team of support workers
- `case_manager`: Assigned case manager

### Contact
Stores contact information for clients including emergency contacts, family, medical professionals, etc.

**Key Fields:**
- `client`: Foreign key to Client
- `contact_type`: Type of contact (emergency, family, guardian, GP, specialist, etc.)
- `first_name`, `last_name`: Contact's name
- `relationship`: Relationship to client
- `phone_primary`, `phone_secondary`: Contact numbers
- `email`: Email address
- `is_primary_contact`: Whether this is the primary contact for this type
- `can_pick_up`: Authorization to pick up client
- `can_receive_updates`: Permission to receive progress updates

### ClientDocument
Manages documents related to clients such as care plans, medical reports, assessments, etc.

**Key Fields:**
- `client`: Foreign key to Client
- `document_type`: Type of document (medical_report, care_plan, assessment, etc.)
- `title`: Document title
- `file_url`: URL to the document file
- `document_date`: Date the document was created/issued
- `expiry_date`: Document expiry date (if applicable)
- `is_confidential`: Whether document is confidential
- `access_restricted_to`: Users who can access confidential documents

## API Endpoints

### Client Endpoints
- `GET /api/v1/clients/clients/` - List all clients
- `POST /api/v1/clients/clients/` - Create new client
- `GET /api/v1/clients/clients/{id}/` - Get client details
- `PUT /api/v1/clients/clients/{id}/` - Update client
- `PATCH /api/v1/clients/clients/{id}/` - Partial update client
- `DELETE /api/v1/clients/clients/{id}/` - Delete client

### Client Custom Actions
- `GET /api/v1/clients/clients/summary/` - Get client summary
- `GET /api/v1/clients/clients/{id}/contacts/` - Get client contacts
- `GET /api/v1/clients/clients/{id}/emergency_contacts/` - Get emergency contacts
- `GET /api/v1/clients/clients/{id}/documents/` - Get client documents
- `GET /api/v1/clients/clients/by_support_worker/` - Get clients by support worker
- `GET /api/v1/clients/clients/by_case_manager/` - Get clients by case manager
- `GET /api/v1/clients/clients/statistics/` - Get client statistics

### Contact Endpoints
- `GET /api/v1/clients/contacts/` - List all contacts
- `POST /api/v1/clients/contacts/` - Create new contact
- `GET /api/v1/clients/contacts/{id}/` - Get contact details
- `PUT /api/v1/clients/contacts/{id}/` - Update contact
- `PATCH /api/v1/clients/contacts/{id}/` - Partial update contact
- `DELETE /api/v1/clients/contacts/{id}/` - Delete contact

### Contact Custom Actions
- `GET /api/v1/clients/contacts/by_type/?type={type}` - Get contacts by type
- `GET /api/v1/clients/contacts/emergency/` - Get all emergency contacts

### Document Endpoints
- `GET /api/v1/clients/documents/` - List all documents
- `POST /api/v1/clients/documents/` - Create new document
- `GET /api/v1/clients/documents/{id}/` - Get document details
- `PUT /api/v1/clients/documents/{id}/` - Update document
- `PATCH /api/v1/clients/documents/{id}/` - Partial update document
- `DELETE /api/v1/clients/documents/{id}/` - Delete document

### Document Custom Actions
- `GET /api/v1/clients/documents/by_type/?type={type}` - Get documents by type
- `GET /api/v1/clients/documents/expiring_soon/` - Get expiring documents

## Serializers

### Client Serializers
- `ClientListSerializer`: Lightweight serializer for client lists
- `ClientDetailSerializer`: Full serializer with related data
- `ClientCreateSerializer`: For creating new clients
- `ClientUpdateSerializer`: For updating existing clients
- `ClientSummarySerializer`: Minimal serializer for references

### Contact Serializers
- `ContactSerializer`: Full contact serializer
- `ContactCreateSerializer`: For creating new contacts
- `ContactUpdateSerializer`: For updating existing contacts

### Document Serializers
- `ClientDocumentSerializer`: Full document serializer
- `ClientDocumentCreateSerializer`: For creating new documents

## Permissions
- All endpoints require authentication
- Non-admin users can only see clients they are assigned to (as primary support worker, team member, or case manager)
- Document access respects confidentiality settings

## Filter Parameters

### Clients
- `gender`: male, female, other, prefer_not_to_say
- `care_level`: low, medium, high, critical
- `is_active`: true, false
- `primary_support_worker`: {user_id}
- `case_manager`: {user_id}
- `search`: first_name, last_name, client_id, diagnosis, interests
- `ordering`: last_name, first_name, date_of_birth, created_at, care_level

### Contacts
- `client`: {client_id}
- `contact_type`: emergency, family, guardian, gp, specialist, therapist, social_worker, advocate, friend, other
- `relationship`: parent, sibling, guardian, grandparent, aunt_uncle, cousin, friend, doctor, therapist, social_worker, advocate, other
- `is_primary_contact`: true, false
- `is_active`: true, false
- `search`: first_name, last_name, phone_primary, email, practice_name
- `ordering`: contact_type, last_name, first_name, created_at

### Documents
- `client`: {client_id}
- `document_type`: medical_report, assessment, care_plan, behavior_plan, consent_form, insurance, legal, photo_id, other
- `is_confidential`: true, false
- `uploaded_by`: {user_id}
- `search`: title, description
- `ordering`: document_date, created_at, title

## Example Usage

### Create a Client
```json
POST /api/v1/clients/clients/
{
  "client_id": "CLI-TV-001",
  "first_name": "Tavonga",
  "last_name": "Mukamuri",
  "date_of_birth": "1990-01-01",
  "gender": "male",
  "diagnosis": "Autism Spectrum Disorder",
  "care_level": "medium",
  "interests": "Music, Art, Swimming",
  "behavioral_triggers": ["loud noises", "crowded spaces"],
  "calming_strategies": ["quiet music", "deep breathing"],
  "is_active": true
}
```

### Create an Emergency Contact
```json
POST /api/v1/clients/contacts/
{
  "client": "{client_id}",
  "contact_type": "emergency",
  "first_name": "John",
  "last_name": "Doe",
  "relationship": "parent",
  "phone_primary": "+1234567890",
  "email": "john.doe@example.com",
  "is_primary_contact": true,
  "can_pick_up": true,
  "can_receive_updates": true
}
```

### Create a Document
```json
POST /api/v1/clients/documents/
{
  "client": "{client_id}",
  "document_type": "care_plan",
  "title": "Tavonga Care Plan 2024",
  "description": "Annual care plan for Tavonga",
  "file_url": "https://example.com/documents/care_plan.pdf",
  "document_date": "2024-01-01",
  "is_confidential": false
}
```

## Testing
Run the test script to verify the app is working correctly:
```bash
python create_test_client.py
```

## Admin Interface
The app includes comprehensive Django admin interfaces for all models with:
- Proper field organization
- Search functionality
- Filtering options
- Inline editing for related models
- Custom display methods

## Database Schema
The app uses SQLite-compatible fields including JSONField for storing arrays. The schema includes:
- Proper foreign key relationships
- Unique constraints
- Indexes for performance
- UUID primary keys for security 