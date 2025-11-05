from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import (
    UserListView,
    UserDetailView,
    UserInactiveListView,
    UserReactivateView,
    UserLoginView,
    UserProfileView
)

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('inactive/', UserInactiveListView.as_view(), name='user-inactive-list'),
    path('<int:user_id>/reactivate/', UserReactivateView.as_view(), name='user-reactivate'),
    path('auth/login/', UserLoginView.as_view(), name='user-login'),
    path('auth/profile/', UserProfileView.as_view(), name='user-profile'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
