"""
URL routing for Core template views
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('tutorial/', views.tutorial_view, name='tutorial'),
    path('company/', views.company_intro_view, name='company_intro'),
]
