"""
Content model for short-form content items
"""
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from apps.core.utils import SoftDeleteManager
from apps.core.constants import (
    CONTENT_STATUS_DRAFT,
    CONTENT_STATUS_PUBLIC,
    CONTENT_STATUS_DELETED,
    CONTENT_STATUS_CHOICES,
    CURRENCY_USD,
    CURRENCY_CHOICES,
    RATING_ALL,
    RATING_CHOICES
)


class Content(models.Model):
    """Short-form content item created by producers"""

    producer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contents',
        limit_choices_to={'role': 'creator'},
        verbose_name='Producer'
    )

    # Basic information
    title = models.CharField(
        max_length=200,
        verbose_name='Title'
    )
    description = models.TextField(
        verbose_name='Description'
    )
    poster = models.ImageField(
        upload_to='posters/',
        blank=True,
        null=True,
        verbose_name='Poster',
        help_text='Vertical poster image for content'
    )

    # Genre tags (1-3 required, using ArrayField for PostgreSQL)
    genre_tags = ArrayField(
        models.CharField(max_length=50),
        size=3,
        verbose_name='Genre tags',
        help_text='1-3 genre tags'
    )

    # Content rating
    rating = models.CharField(
        max_length=3,
        choices=RATING_CHOICES,
        default=RATING_ALL,
        verbose_name='Age rating',
        help_text='Content age restriction'
    )

    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Price'
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default=CURRENCY_USD,
        verbose_name='Currency'
    )

    # Content details
    duration_seconds = models.PositiveIntegerField(
        verbose_name='Duration (seconds)',
        help_text='Video duration in seconds'
    )
    video_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='Video URL',
        help_text='URL to video preview or full video'
    )
    screener_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='Screener URL',
        help_text='Internal screener video with watermark'
    )
    release_target = models.DateField(
        blank=True,
        null=True,
        verbose_name='Target release date',
        help_text='Desired release date for the content'
    )

    # Status and visibility
    status = models.CharField(
        max_length=20,
        choices=CONTENT_STATUS_CHOICES,
        default=CONTENT_STATUS_DRAFT,
        db_index=True,
        verbose_name='Status'
    )

    # Statistics
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name='View count'
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
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Deleted at'
    )

    # Managers
    objects = models.Manager()  # Default manager
    active_objects = SoftDeleteManager()  # Excludes soft-deleted items

    class Meta:
        verbose_name = 'Content'
        verbose_name_plural = 'Contents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['producer', 'status']),
        ]

    def __str__(self):
        return f"{self.title} by {self.producer.username}"

    @property
    def is_public(self):
        """Check if content is publicly visible"""
        return self.status == CONTENT_STATUS_PUBLIC

    @property
    def is_deleted(self):
        """Check if content is soft-deleted"""
        return self.status == CONTENT_STATUS_DELETED

    def soft_delete(self):
        """Soft delete this content"""
        from django.utils import timezone
        self.status = CONTENT_STATUS_DELETED
        self.deleted_at = timezone.now()
        self.save(update_fields=['status', 'deleted_at'])

    def increment_view_count(self):
        """Increment view count (atomic operation)"""
        from django.db.models import F
        Content.objects.filter(pk=self.pk).update(view_count=F('view_count') + 1)
        self.refresh_from_db(fields=['view_count'])
