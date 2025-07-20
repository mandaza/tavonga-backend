from django.shortcuts import render
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Client, Contact, ClientDocument
from .serializers import (
    ClientListSerializer, ClientDetailSerializer, ClientCreateSerializer,
    ClientUpdateSerializer, ClientSummarySerializer,
    ContactSerializer, ContactCreateSerializer, ContactUpdateSerializer,
    ClientDocumentSerializer, ClientDocumentCreateSerializer
)

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "is_admin", False)

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['gender', 'care_level', 'is_active', 'primary_support_worker', 'case_manager']
    search_fields = ['first_name', 'last_name', 'client_id', 'diagnosis', 'interests']
    ordering_fields = ['last_name', 'first_name', 'date_of_birth', 'created_at', 'care_level']
    ordering = ['last_name', 'first_name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClientCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ClientUpdateSerializer
        elif self.action == 'list':
            return ClientListSerializer
        elif self.action == 'summary':
            return ClientSummarySerializer
        return ClientDetailSerializer
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Client.objects.none()
        
        queryset = Client.objects.select_related(
            'primary_support_worker', 'case_manager'
        ).prefetch_related(
            'support_team',
            Prefetch('contacts', queryset=Contact.objects.filter(is_active=True)),
            'documents'
        )
        
        # Filter based on user permissions
        if not self.request.user.is_admin:
            # Support workers can only see clients assigned to them
            queryset = queryset.filter(
                Q(primary_support_worker=self.request.user) |
                Q(support_team=self.request.user) |
                Q(case_manager=self.request.user)
            ).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        # Auto-generate client_id if not provided
        if not serializer.validated_data.get('client_id'):
            # Generate client ID based on initials and timestamp
            first_initial = serializer.validated_data['first_name'][0].upper()
            last_initial = serializer.validated_data['last_name'][0].upper()
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M')
            client_id = f"CLI-{first_initial}{last_initial}-{timestamp}"
            serializer.validated_data['client_id'] = client_id
        
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get a summary list of all clients"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = ClientSummarySerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """Get all contacts for a specific client"""
        client = self.get_object()
        contacts = client.contacts.filter(is_active=True).order_by('contact_type', 'is_primary_contact')
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def emergency_contacts(self, request, pk=None):
        """Get emergency contacts for a specific client"""
        client = self.get_object()
        emergency_contacts = client.contacts.filter(
            contact_type='emergency', 
            is_active=True
        ).order_by('is_primary_contact')
        serializer = ContactSerializer(emergency_contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Get all documents for a specific client"""
        client = self.get_object()
        documents = client.documents.all().order_by('-document_date', '-created_at')
        
        # Filter confidential documents based on permissions
        if not request.user.is_admin:
            documents = documents.filter(
                Q(is_confidential=False) |
                Q(access_restricted_to=request.user)
            )
        
        serializer = ClientDocumentSerializer(documents, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_support_worker(self, request):
        """Get clients assigned to the current user as support worker"""
        queryset = self.get_queryset().filter(
            Q(primary_support_worker=request.user) |
            Q(support_team=request.user)
        ).distinct()
        
        serializer = ClientListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_case_manager(self, request):
        """Get clients managed by the current user"""
        queryset = self.get_queryset().filter(case_manager=request.user)
        serializer = ClientListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get client statistics"""
        queryset = self.get_queryset()
        
        stats = {
            'total_clients': queryset.count(),
            'active_clients': queryset.filter(is_active=True).count(),
            'by_care_level': {
                level[0]: queryset.filter(care_level=level[0]).count()
                for level in Client.CARE_LEVEL_CHOICES
            },
            'by_gender': {
                gender[0]: queryset.filter(gender=gender[0]).count()
                for gender in Client.GENDER_CHOICES
            },
            'with_emergency_contacts': queryset.filter(
                contacts__contact_type='emergency',
                contacts__is_active=True
            ).distinct().count(),
            'recent_additions': queryset.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()
        }
        
        return Response(stats)


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['client', 'contact_type', 'relationship', 'is_primary_contact', 'is_active']
    search_fields = ['first_name', 'last_name', 'phone_primary', 'email', 'practice_name']
    ordering_fields = ['contact_type', 'last_name', 'first_name', 'created_at']
    ordering = ['contact_type', 'is_primary_contact', 'last_name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ContactCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ContactUpdateSerializer
        return ContactSerializer
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Contact.objects.none()
        
        queryset = Contact.objects.select_related('client')
        
        # Filter based on user permissions - only contacts for accessible clients
        if not self.request.user.is_admin:
            queryset = queryset.filter(
                Q(client__primary_support_worker=self.request.user) |
                Q(client__support_team=self.request.user) |
                Q(client__case_manager=self.request.user)
            ).distinct()
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get contacts grouped by type"""
        contact_type = request.query_params.get('type')
        if not contact_type:
            return Response({'error': 'type parameter is required'}, status=400)
        
        queryset = self.filter_queryset(self.get_queryset()).filter(
            contact_type=contact_type,
            is_active=True
        )
        serializer = ContactSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def emergency(self, request):
        """Get all emergency contacts"""
        queryset = self.filter_queryset(self.get_queryset()).filter(
            contact_type='emergency',
            is_active=True
        ).order_by('client__last_name', 'is_primary_contact')
        
        serializer = ContactSerializer(queryset, many=True)
        return Response(serializer.data)


class ClientDocumentViewSet(viewsets.ModelViewSet):
    queryset = ClientDocument.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['client', 'document_type', 'is_confidential', 'uploaded_by']
    search_fields = ['title', 'description']
    ordering_fields = ['document_date', 'created_at', 'title']
    ordering = ['-document_date', '-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClientDocumentCreateSerializer
        return ClientDocumentSerializer
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return ClientDocument.objects.none()
        
        queryset = ClientDocument.objects.select_related('client', 'uploaded_by')
        
        # Filter based on user permissions
        if not self.request.user.is_admin:
            # Only documents for accessible clients and non-confidential or specifically granted access
            queryset = queryset.filter(
                Q(client__primary_support_worker=self.request.user) |
                Q(client__support_team=self.request.user) |
                Q(client__case_manager=self.request.user)
            ).filter(
                Q(is_confidential=False) |
                Q(access_restricted_to=self.request.user)
            ).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get documents by type"""
        document_type = request.query_params.get('type')
        if not document_type:
            return Response({'error': 'type parameter is required'}, status=400)
        
        queryset = self.filter_queryset(self.get_queryset()).filter(
            document_type=document_type
        )
        serializer = ClientDocumentSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get documents expiring within the next 30 days"""
        from datetime import date, timedelta
        expiry_date = date.today() + timedelta(days=30)
        
        queryset = self.filter_queryset(self.get_queryset()).filter(
            expiry_date__lte=expiry_date,
            expiry_date__gte=date.today()
        )
        serializer = ClientDocumentSerializer(queryset, many=True)
        return Response(serializer.data)
