from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import MediaFile
from .serializers import MediaFileSerializer

# Create your views here.

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (obj.uploaded_by == request.user or getattr(request.user, 'is_admin', False))

class MediaFileViewSet(viewsets.ModelViewSet):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return MediaFile.objects.none()
        
        if self.request.user.is_authenticated and getattr(self.request.user, 'is_admin', False):
            return MediaFile.objects.all()
        return MediaFile.objects.filter(uploaded_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not (instance.uploaded_by == request.user or getattr(request.user, 'is_admin', False)):
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
