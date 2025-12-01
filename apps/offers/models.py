"""
Offer model for buyer-producer negotiations
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from apps.core.constants import (
    OFFER_STATUS_PENDING,
    OFFER_STATUS_ACCEPTED,
    OFFER_STATUS_REJECTED,
    OFFER_STATUS_EXPIRED,
    OFFER_STATUS_CHOICES,
    CURRENCY_USD,
    CURRENCY_CHOICES
)


class Offer(models.Model):
    """Offer from buyer to producer for content purchase"""

    content = models.ForeignKey(
        'contents.Content',
        on_delete=models.CASCADE,
        related_name='offer_set',
        verbose_name='Content'
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='buyer_offers',
        limit_choices_to={'role': 'buyer'},
        verbose_name='Buyer'
    )

    # Offer details
    offered_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Offered price'
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default=CURRENCY_USD,
        verbose_name='Currency'
    )
    message = models.TextField(
        blank=True,
        verbose_name='Message to producer',
        help_text='Optional message from buyer'
    )

    # Status and expiry
    status = models.CharField(
        max_length=20,
        choices=OFFER_STATUS_CHOICES,
        default=OFFER_STATUS_PENDING,
        db_index=True,
        verbose_name='Status'
    )
    validity_days = models.PositiveIntegerField(
        default=7,
        verbose_name='Validity (days)',
        help_text='Number of days this offer is valid'
    )
    expires_at = models.DateTimeField(
        verbose_name='Expires at',
        help_text='Calculated expiry date'
    )

    # Response tracking
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Responded at'
    )
    producer_response = models.TextField(
        blank=True,
        verbose_name='Producer response',
        help_text='Optional message from producer'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Created at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at'
    )

    class Meta:
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['content', 'status']),
            models.Index(fields=['status', 'expires_at']),
        ]
        constraints = [
            # Only one pending offer per content/buyer combination
            models.UniqueConstraint(
                fields=['content', 'buyer'],
                condition=models.Q(status=OFFER_STATUS_PENDING),
                name='unique_pending_offer_per_content_buyer'
            )
        ]

    def __str__(self):
        return f"Offer by {self.buyer.username} for {self.content.title} - {self.status}"

    @property
    def producer(self):
        """Get the producer from content"""
        return self.content.producer

    @property
    def is_pending(self):
        """Check if offer is pending"""
        return self.status == OFFER_STATUS_PENDING

    @property
    def is_expired(self):
        """Check if offer has expired"""
        return timezone.now() > self.expires_at

    def save(self, *args, **kwargs):
        """Auto-calculate expires_at on creation"""
        if not self.pk and not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=self.validity_days)
        super().save(*args, **kwargs)

    def accept(self, producer_response=''):
        """Accept this offer"""
        if self.status != OFFER_STATUS_PENDING:
            raise ValueError(f"Cannot accept offer with status: {self.status}")

        if self.is_expired:
            raise ValueError("Cannot accept expired offer")

        self.status = OFFER_STATUS_ACCEPTED
        self.responded_at = timezone.now()
        self.producer_response = producer_response
        self.save(update_fields=['status', 'responded_at', 'producer_response', 'updated_at'])

    def reject(self, producer_response=''):
        """Reject this offer"""
        if self.status != OFFER_STATUS_PENDING:
            raise ValueError(f"Cannot reject offer with status: {self.status}")

        self.status = OFFER_STATUS_REJECTED
        self.responded_at = timezone.now()
        self.producer_response = producer_response
        self.save(update_fields=['status', 'responded_at', 'producer_response', 'updated_at'])

    def mark_as_expired(self):
        """Mark offer as expired (called by scheduled task)"""
        if self.status == OFFER_STATUS_PENDING and self.is_expired:
            self.status = OFFER_STATUS_EXPIRED
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False
