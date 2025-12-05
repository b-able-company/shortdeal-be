"""
Serializers for Content model
"""
from rest_framework import serializers
from .models import Content
from apps.accounts.serializers import UserSerializer
from apps.core.validators import validate_genre_tags


class ContentPublicSerializer(serializers.ModelSerializer):
    """Public serializer for content browsing (read-only)"""

    producer_name = serializers.CharField(source='producer.company_name', read_only=True)
    producer_username = serializers.CharField(source='producer.username', read_only=True)
    booth_slug = serializers.CharField(source='producer.booth_slug', read_only=True)

    class Meta:
        model = Content
        fields = (
            'id', 'title', 'description', 'poster', 'rating',
            'genre_tags', 'price', 'currency', 'duration_seconds',
            'release_target', 'view_count', 'created_at',
            'producer_name', 'producer_username', 'booth_slug'
        )
        read_only_fields = fields


class ContentDetailSerializer(serializers.ModelSerializer):
    """Detailed content serializer with video URL (read-only for buyers)"""

    producer_name = serializers.CharField(source='producer.company_name', read_only=True)
    producer_username = serializers.CharField(source='producer.username', read_only=True)
    booth_slug = serializers.CharField(source='producer.booth_slug', read_only=True)

    class Meta:
        model = Content
        fields = (
            'id', 'title', 'description', 'poster', 'rating',
            'genre_tags', 'price', 'currency', 'duration_seconds',
            'video_url', 'screener_url', 'release_target',
            'view_count', 'created_at', 'updated_at',
            'producer_name', 'producer_username', 'booth_slug'
        )
        read_only_fields = fields


class ContentProducerSerializer(serializers.ModelSerializer):
    """Serializer for producer CRUD operations"""

    class Meta:
        model = Content
        fields = (
            'id', 'title', 'description', 'poster', 'rating',
            'genre_tags', 'price', 'currency', 'duration_seconds',
            'video_url', 'screener_url', 'release_target',
            'status', 'view_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'view_count', 'created_at', 'updated_at')

    def validate_genre_tags(self, value):
        """Validate genre tags (1-3 required)"""
        return validate_genre_tags(value)

    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_duration_seconds(self, value):
        """Validate duration is positive"""
        if value <= 0:
            raise serializers.ValidationError("Duration must be greater than 0.")
        return value

    def create(self, validated_data):
        """Create content with current user as producer"""
        user = self.context['request'].user
        validated_data['producer'] = user
        return super().create(validated_data)


class ContentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating content (supports multipart)"""

    class Meta:
        model = Content
        fields = (
            'title', 'description', 'poster', 'rating',
            'genre_tags', 'price', 'currency', 'duration_seconds',
            'video_url', 'screener_url', 'release_target', 'status'
        )

    def validate_genre_tags(self, value):
        """Validate genre tags (1-3 required)"""
        return validate_genre_tags(value)

    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_duration_seconds(self, value):
        """Validate duration is positive"""
        if value <= 0:
            raise serializers.ValidationError("Duration must be greater than 0.")
        return value
