from django.urls import path
from .views import BehaviorLogReportView, ActivityLogReportView, ShiftReportView, GoalProgressReportView

urlpatterns = [
    path('behaviors/', BehaviorLogReportView.as_view(), name='behavior-log-report'),
    path('activities/', ActivityLogReportView.as_view(), name='activity-log-report'),
    path('shifts/', ShiftReportView.as_view(), name='shift-report'),
    path('goals/', GoalProgressReportView.as_view(), name='goal-progress-report'),
] 