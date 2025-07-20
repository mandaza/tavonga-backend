from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Shift
from .serializers import (
    ShiftSerializer, ShiftCreateSerializer, ShiftUpdateSerializer,
    ShiftListSerializer, ShiftClockInSerializer, ShiftClockOutSerializer, ShiftScheduleSerializer
)

# Create your views here.

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "is_admin", False)

class IsCarerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (getattr(request.user, "is_admin", False) or obj.carer == request.user)

class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['carer', 'date', 'status', 'shift_type']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ShiftCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ShiftUpdateSerializer
        elif self.action == 'list':
            return ShiftListSerializer
        elif self.action == 'clock_in':
            return ShiftClockInSerializer
        elif self.action == 'clock_out':
            return ShiftClockOutSerializer
        elif self.action == 'schedule':
            return ShiftScheduleSerializer
        return ShiftSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        elif self.action in ['retrieve', 'update', 'partial_update', 'clock_in', 'clock_out']:
            return [IsCarerOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Shift.objects.none()
        
        if self.request.user.is_admin:
            return Shift.objects.all()
        return Shift.objects.filter(carer=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def clock_in(self, request, pk=None):
        shift = self.get_object()
        serializer = ShiftClockInSerializer(shift, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ShiftSerializer(shift).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def clock_out(self, request, pk=None):
        shift = self.get_object()
        serializer = ShiftClockOutSerializer(shift, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ShiftSerializer(shift).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_shifts(self, request):
        shifts = self.get_queryset()
        serializer = ShiftListSerializer(shifts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def schedule(self, request):
        shifts = self.get_queryset().filter(status__in=['scheduled', 'in_progress'])
        serializer = ShiftScheduleSerializer(shifts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        from django.utils import timezone
        today = timezone.now().date()
        shifts = self.get_queryset().filter(date=today)
        serializer = ShiftListSerializer(shifts, many=True)
        return Response(serializer.data)
