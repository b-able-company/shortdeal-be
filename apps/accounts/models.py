from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model - Creator/Buyer/Admin role distinction"""

    class Role(models.TextChoices):
        CREATOR = 'creator', 'Creator'
        BUYER = 'buyer', 'Buyer'
        ADMIN = 'admin', 'Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CREATOR,
        verbose_name='Role'
    )

    # Onboarding fields
    is_onboarded = models.BooleanField(default=False, verbose_name='Onboarding completed')

    # Company information
    company_name = models.CharField(max_length=200, blank=True, verbose_name='Company name')
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, verbose_name='Company logo')
    country = models.CharField(max_length=100, blank=True, verbose_name='Country')

    # Genre tags (for creators only)
    genre_tags = models.JSONField(default=list, blank=True, verbose_name='Genre tags')

    # Contact information
    phone = models.CharField(max_length=20, blank=True, verbose_name='Phone number')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated at')

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
