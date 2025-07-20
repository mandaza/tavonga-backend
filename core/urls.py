"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from . import views

schema_view = get_schema_view(
    openapi.Info(
        title="Tavonga CareConnect API",
        default_version='v1',
        description="API for Tavonga Autism & Intellectual Disability Support System",
        terms_of_service="https://www.tavonga.com/terms/",
        contact=openapi.Contact(email="admin@tavonga.com"),
        license=openapi.License(name="Private License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

def dashboard_stats(request):
    """Dashboard statistics endpoint"""
    from django.contrib.auth import get_user_model
    from behaviors.models import BehaviorLog
    from activities.models import ActivityLog
    from shifts.models import Shift
    
    User = get_user_model()
    today = timezone.now().date()
    
    # Get basic stats
    total_carers = User.objects.filter(is_admin=False).count()
    active_carers = User.objects.filter(is_admin=False, is_active=True).count()
    
    # Get today's behaviors
    behaviors_today = BehaviorLog.objects.filter(date=today).count()
    
    # Get completed activities today
    activities_completed = ActivityLog.objects.filter(
        date=today, 
        completed=True
    ).count()
    
    # Get active shifts today
    active_shifts = Shift.objects.filter(
        date=today,
        status='in_progress'
    ).count()
    
    return JsonResponse({
        'total_carers': total_carers,
        'active_carers': active_carers,
        'behaviors_today': behaviors_today,
        'activities_completed': activities_completed,
        'active_shifts': active_shifts,
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    # JWT Authentication
    path('api/v1/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # API endpoints
    path('api/v1/', include('users.urls')),
    path('api/v1/', include('goals.urls')),
    path('api/v1/', include('activities.urls')),
    path('api/v1/', include('behaviors.urls')),
    path('api/v1/', include('shifts.urls')),
    path('api/v1/', include('media.urls')),
    path('api/v1/reports/', include('reports.urls')),
    path('api/v1/scheduler/', include('scheduler.urls')),
    path('api/v1/', include('clients.urls')),
    path('api/v1/dashboard/stats', dashboard_stats, name='dashboard-stats-no-slash'),
    path('api/v1/dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    # Health check endpoints
    path('api/v1/health/', views.health_check, name='health-check'),
    path('api/v1/ready/', views.ready_check, name='ready-check'),
    path('api/v1/live/', views.live_check, name='live-check'),
    path('health/', views.health_check, name='health-check-short'),  # For load balancers
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
