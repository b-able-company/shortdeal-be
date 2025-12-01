"""
API URL routing for LOI endpoints
"""
from django.urls import path
from .api_views import LOIListView, LOIDetailView, LOIPDFDownloadView

app_name = 'loi_api'

urlpatterns = [
    path('', LOIListView.as_view(), name='loi_list'),
    path('<int:pk>/', LOIDetailView.as_view(), name='loi_detail'),
    path('<int:pk>/pdf/', LOIPDFDownloadView.as_view(), name='loi_pdf_download'),
]
