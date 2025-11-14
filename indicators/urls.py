from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    IndicatorViewSet,
    IndicatorValueViewSet,
    IndicatorTargetViewSet,
    IndicatorComputationView,
    FormulaValidationView,
    IndicatorPreviewView
)

router = DefaultRouter()
router.register(r'', IndicatorViewSet, basename='indicator')
router.register(r'values', IndicatorValueViewSet, basename='indicator-value')
router.register(r'targets', IndicatorTargetViewSet, basename='indicator-target')

urlpatterns = [
    # Specific paths must come BEFORE the router to avoid being intercepted
    path('compute/<int:survey_id>/', IndicatorComputationView.as_view(), name='compute-indicators'),
    path('validate-formula/', FormulaValidationView.as_view(), name='validate-formula'),
    path('preview/', IndicatorPreviewView.as_view(), name='preview-indicator'),
    # Router must be last to avoid intercepting specific paths
    path('', include(router.urls)),
]

