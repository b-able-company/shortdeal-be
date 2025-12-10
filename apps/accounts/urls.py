from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path('onboarding/producer/', views.onboarding_producer_view, name='onboarding_producer'),
    path('onboarding/buyer/', views.onboarding_buyer_view, name='onboarding_buyer'),

    # Password Reset
    path('password-reset/', views.password_reset_request_view, name='password_reset_request'),
    path('password-reset/confirm/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
]
