from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IndicatorViewSet, IndicatorValueViewSet, IndicatorTargetViewSet, IndicatorComputationView

router = DefaultRouter()
router.register(r'indicators', IndicatorViewSet, basename='indicator')
router.register(r'values', IndicatorValueViewSet, basename='indicator-value')
router.register(r'targets', IndicatorTargetViewSet, basename='indicator-target')

urlpatterns = [
    path('', include(router.urls)),
    path('compute/<int:survey_id>/', IndicatorComputationView.as_view(), name='compute-indicators'),
]

