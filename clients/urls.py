from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientViewSet, ContactViewSet, ClientDocumentViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'clients', ClientViewSet)
router.register(r'contacts', ContactViewSet)
router.register(r'documents', ClientDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 