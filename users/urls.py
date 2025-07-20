from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 