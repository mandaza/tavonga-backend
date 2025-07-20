from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivityViewSet, ActivityLogViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'activities', ActivityViewSet)

# Separate router for activity logs to avoid URL conflicts
logs_router = DefaultRouter(trailing_slash=False)
logs_router.register(r'logs', ActivityLogViewSet, basename='activity-logs')

urlpatterns = [
    path('', include(router.urls)),
    path('activities/', include(logs_router.urls)),
] 