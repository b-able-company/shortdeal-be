"""
Admin configuration for Offer model
"""
from django.contrib import admin
from .models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'content', 'offered_price', 'currency', 'status', 'expires_at', 'created_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('buyer__username', 'content__title', 'message')
    readonly_fields = ('created_at', 'updated_at', 'responded_at', 'expires_at')
    list_per_page = 50

    fieldsets = (
        ('Offer Details', {
            'fields': ('content', 'buyer', 'offered_price', 'currency', 'message')
        }),
        ('Status & Expiry', {
            'fields': ('status', 'validity_days', 'expires_at')
        }),
        ('Producer Response', {
            'fields': ('responded_at', 'producer_response')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('buyer', 'content', 'content__producer')
