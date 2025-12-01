"""
API URL routing for authentication endpoints
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .api_views import (
    RegisterView,
    LoginView,
    ProfileView,
    OnboardingProducerView,
    OnboardingBuyerView,
    ChangePasswordView,
    LogoutView
)

app_name = 'accounts_api'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile
    path('me/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),

    # Onboarding
    path('onboarding/producer/', OnboardingProducerView.as_view(), name='onboarding_producer'),
    path('onboarding/buyer/', OnboardingBuyerView.as_view(), name='onboarding_buyer'),
]
