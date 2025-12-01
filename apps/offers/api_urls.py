"""
API URL routing for offer endpoints
"""
from django.urls import path
from .api_views import (
    BuyerOfferListCreateView,
    BuyerOfferDetailView,
    ProducerOfferListView,
    ProducerOfferDetailView,
    ProducerOfferAcceptView,
    ProducerOfferRejectView
)

app_name = 'offers_api'

urlpatterns = [
    # Buyer endpoints
    path('buyer/', BuyerOfferListCreateView.as_view(), name='buyer_offer_list_create'),
    path('buyer/<int:pk>/', BuyerOfferDetailView.as_view(), name='buyer_offer_detail'),

    # Producer endpoints
    path('producer/', ProducerOfferListView.as_view(), name='producer_offer_list'),
    path('producer/<int:pk>/', ProducerOfferDetailView.as_view(), name='producer_offer_detail'),
    path('producer/<int:pk>/accept/', ProducerOfferAcceptView.as_view(), name='producer_offer_accept'),
    path('producer/<int:pk>/reject/', ProducerOfferRejectView.as_view(), name='producer_offer_reject'),
]
