from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import time
import os


def health_check(request):
    """
    Health check endpoint for monitoring and load balancers.
    Returns system status and basic metrics.
    """
    status = "healthy"
    checks = {}
    
    # Database connectivity check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
        status = "unhealthy"
    
    # Cache connectivity check (if configured)
    if hasattr(settings, 'CACHES') and 'default' in settings.CACHES:
        try:
            cache.set('health_check', 'ok', 30)
            cache_value = cache.get('health_check')
            if cache_value == 'ok':
                checks["cache"] = "healthy"
            else:
                checks["cache"] = "unhealthy: cache test failed"
                status = "degraded"
        except Exception as e:
            checks["cache"] = f"unhealthy: {str(e)}"
            status = "degraded"
    else:
        checks["cache"] = "not_configured"
    
    # Disk space check
    try:
        disk_usage = os.statvfs('.')
        free_space = disk_usage.f_bavail * disk_usage.f_frsize
        total_space = disk_usage.f_blocks * disk_usage.f_frsize
        free_percentage = (free_space / total_space) * 100
        
        if free_percentage > 10:
            checks["disk_space"] = f"healthy: {free_percentage:.1f}% free"
        elif free_percentage > 5:
            checks["disk_space"] = f"warning: {free_percentage:.1f}% free"
            status = "degraded"
        else:
            checks["disk_space"] = f"critical: {free_percentage:.1f}% free"
            status = "unhealthy"
    except Exception as e:
        checks["disk_space"] = f"unknown: {str(e)}"
    
    response_data = {
        "status": status,
        "timestamp": int(time.time()),
        "version": "1.0.0",
        "environment": "production" if not settings.DEBUG else "development",
        "checks": checks
    }
    
    # Return appropriate HTTP status code
    if status == "healthy":
        return JsonResponse(response_data, status=200)
    elif status == "degraded":
        return JsonResponse(response_data, status=200)  # Still OK but with warnings
    else:
        return JsonResponse(response_data, status=503)  # Service Unavailable


def ready_check(request):
    """
    Readiness check endpoint for Kubernetes deployments.
    Returns 200 if the app is ready to serve traffic.
    """
    try:
        # Basic database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({"status": "ready"}, status=200)
    except Exception:
        return JsonResponse({"status": "not_ready"}, status=503)


def live_check(request):
    """
    Liveness check endpoint for Kubernetes deployments.
    Returns 200 if the app is alive (basic functionality).
    """
    return JsonResponse({
        "status": "alive",
        "timestamp": int(time.time())
    }, status=200)


def swagger_test(request):
    """
    Simple test endpoint for Swagger UI testing.
    This endpoint can be used to verify that the API is accessible via HTTPS.
    """
    return JsonResponse({
        "message": "✅ Swagger test successful!",
        "protocol": request.META.get('HTTP_X_FORWARDED_PROTO', 'unknown'),
        "host": request.META.get('HTTP_HOST', 'unknown'),
        "secure": request.is_secure(),
        "timestamp": int(time.time()),
        "method": request.method
    }) 