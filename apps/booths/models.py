"""
Booth model for producer profiles
"""
from django.db import models
from django.conf import settings


class Booth(models.Model):
    """Producer booth - auto-created when producer signs up"""

    producer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='booth',
        limit_choices_to={'role': 'creator'},
        verbose_name='Producer'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='Booth slug'
    )
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name='View count'
    )
    is_boosted = models.BooleanField(
        default=False,
        verbose_name='Is boosted'
    )
    boost_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Boost expires at'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at'
    )

    class Meta:
        verbose_name = 'Booth'
        verbose_name_plural = 'Booths'
        ordering = ['-created_at']

    def __str__(self):
        return f"Booth: {self.slug} ({self.producer.username})"

    @property
    def is_boost_active(self):
        """Check if boost is currently active"""
        if not self.is_boosted:
            return False
        if self.boost_expires_at is None:
            return False
        from django.utils import timezone
        return timezone.now() < self.boost_expires_at

    def increment_view_count(self):
        """Increment view count atomically"""
        from django.db.models import F
        Booth.objects.filter(pk=self.pk).update(view_count=F('view_count') + 1)
