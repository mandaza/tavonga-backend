from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ScheduleViewSet, ScheduleTemplateViewSet, 
    ScheduleReminderViewSet, ScheduleConflictViewSet
)

router = DefaultRouter(trailing_slash=False)
router.register(r'schedules', ScheduleViewSet)
router.register(r'templates', ScheduleTemplateViewSet)
router.register(r'reminders', ScheduleReminderViewSet)
router.register(r'conflicts', ScheduleConflictViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 