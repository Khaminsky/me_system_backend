from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, DocumentCategoryViewSet, DocumentAccessViewSet

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'categories', DocumentCategoryViewSet, basename='category')
router.register(r'access-logs', DocumentAccessViewSet, basename='access-log')

urlpatterns = [
    path('', include(router.urls)),
]

