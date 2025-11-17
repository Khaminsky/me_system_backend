from django.urls import path
from .views import SystemSettingsView, SystemSettingsPublicView

urlpatterns = [
    path('', SystemSettingsView.as_view(), name='system-settings'),
    path('public/', SystemSettingsPublicView.as_view(), name='system-settings-public'),
]

