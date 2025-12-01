"""
Studio API URL routing for producer content management
"""
from django.urls import path
from .studio_views import (
    StudioContentListCreateView,
    StudioContentDetailView,
    StudioContentStatsView
)

app_name = 'studio_contents'

urlpatterns = [
    # Producer content management
    path('', StudioContentListCreateView.as_view(), name='content_list_create'),
    path('stats/', StudioContentStatsView.as_view(), name='content_stats'),
    path('<int:pk>/', StudioContentDetailView.as_view(), name='content_detail'),
]
