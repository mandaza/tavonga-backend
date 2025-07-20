from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, UserListSerializer,
    UserUpdateSerializer, AdminUserSerializer
)

User = get_user_model()

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "is_admin", False)

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and (getattr(request.user, "is_admin", False) or obj == request.user)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            if self.request.user.is_authenticated and getattr(self.request.user, "is_admin", False):
                return AdminUserSerializer
            return UserProfileSerializer
        elif self.action == 'list':
            return UserListSerializer
        return UserListSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [permissions.AllowAny()]
        elif self.action in ['logout']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['list', 'destroy']:
            return [IsAdminUser()]
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return [IsOwnerOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        
        if self.request.user.is_admin:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(email=email, password=password)
        
        if user:
            if not user.is_active:
                return Response(
                    {'error': 'Account is disabled'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not user.approved and not user.is_admin:
                return Response(
                    {'error': 'Account is pending approval'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            refresh = RefreshToken.for_user(user)
            serializer = UserProfileSerializer(user)
            
            return Response({
                'user': serializer.data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            })
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            # Get the refresh token from request data
            refresh_token = request.data.get('refresh_token')
            
            if refresh_token:
                try:
                    # Try to blacklist the refresh token
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except Exception as e:
                    # If blacklisting fails (not configured), just continue
                    pass
            
            return Response(
                {'message': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'message': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserProfileSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if not request.user.is_admin:
            return Response(
                {'error': 'Only admins can approve users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(pk=pk)
            user.approved = True
            user.save()
            return Response({'message': 'User approved successfully'})
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        if not request.user.is_admin:
            return Response(
                {'error': 'Only admins can disable users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(pk=pk)
            user.is_active = False
            user.save()
            return Response({'message': 'User disabled successfully'})
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        if not request.user.is_admin:
            return Response(
                {'error': 'Only admins can enable users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = User.objects.get(pk=pk)
            user.is_active = True
            user.save()
            return Response({'message': 'User enabled successfully'})
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
