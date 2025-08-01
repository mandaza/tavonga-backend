from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShiftViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'shifts', ShiftViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 