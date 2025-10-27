from django.urls import path
from .views import SurveyUploadView, SurveyListView

urlpatterns = [
    path('upload/', SurveyUploadView.as_view(), name='survey-upload'),
    path('', SurveyListView.as_view(), name='survey-list'),
]
