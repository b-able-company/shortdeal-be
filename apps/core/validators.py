"""
Custom validators for file uploads and data validation
"""
from django.core.exceptions import ValidationError
from .constants import MAX_LOGO_SIZE, MAX_POSTER_SIZE, ALLOWED_IMAGE_TYPES


def validate_logo_size(file):
    """Validate logo file size (max 2MB)"""
    if file.size > MAX_LOGO_SIZE:
        raise ValidationError(f'Logo file size must be under {MAX_LOGO_SIZE / (1024*1024)}MB.')


def validate_poster_size(file):
    """Validate poster file size (max 5MB)"""
    if file.size > MAX_POSTER_SIZE:
        max_mb = MAX_POSTER_SIZE / (1024*1024)
        raise ValidationError(f'Poster file size must be under {max_mb}MB.')


def validate_image_type(file):
    """Validate image file type (JPEG, PNG only)"""
    if hasattr(file, 'content_type'):
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise ValidationError(f'Image must be JPEG or PNG format. Got: {file.content_type}')


def validate_genre_tags(tags):
    """Validate genre tags (1-3 items required)"""
    if not isinstance(tags, list):
        raise ValidationError('Genre tags must be a list.')
    if len(tags) < 1:
        raise ValidationError('At least 1 genre tag is required.')
    if len(tags) > 3:
        raise ValidationError('Maximum 3 genre tags allowed.')
    return tags


def validate_price_range(min_price, max_price):
    """Validate price range (min <= max)"""
    if min_price is not None and max_price is not None:
        if min_price > max_price:
            raise ValidationError('Minimum price cannot be greater than maximum price.')
