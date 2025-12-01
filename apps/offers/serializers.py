"""
Serializers for Offer model
"""
from rest_framework import serializers
from .models import Offer
from apps.contents.serializers import ContentPublicSerializer


class OfferBuyerSerializer(serializers.ModelSerializer):
    """Serializer for buyer's offer operations"""

    content_title = serializers.CharField(source='content.title', read_only=True)
    producer_name = serializers.CharField(source='content.producer.company_name', read_only=True)

    class Meta:
        model = Offer
        fields = (
            'id', 'content', 'content_title', 'producer_name',
            'offered_price', 'currency', 'message', 'validity_days',
            'status', 'expires_at', 'responded_at', 'producer_response',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'status', 'expires_at', 'responded_at', 'producer_response', 'created_at', 'updated_at')

    def validate_offered_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Offered price must be greater than 0.")
        return value

    def validate(self, attrs):
        """Validate content is public and not deleted"""
        content = attrs.get('content')
        if content and content.status != 'public':
            raise serializers.ValidationError("Cannot make offer on non-public content.")

        # Check duplicate pending offer
        buyer = self.context['request'].user
        if Offer.objects.filter(content=content, buyer=buyer, status='pending').exists():
            raise serializers.ValidationError("You already have a pending offer for this content.")

        return attrs


class OfferProducerSerializer(serializers.ModelSerializer):
    """Serializer for producer's offer view"""

    buyer_name = serializers.CharField(source='buyer.company_name', read_only=True)
    buyer_username = serializers.CharField(source='buyer.username', read_only=True)
    buyer_country = serializers.CharField(source='buyer.country', read_only=True)
    content_title = serializers.CharField(source='content.title', read_only=True)

    class Meta:
        model = Offer
        fields = (
            'id', 'content', 'content_title',
            'buyer', 'buyer_name', 'buyer_username', 'buyer_country',
            'offered_price', 'currency', 'message', 'validity_days',
            'status', 'expires_at', 'responded_at', 'producer_response',
            'created_at', 'updated_at'
        )
        read_only_fields = fields


class OfferResponseSerializer(serializers.Serializer):
    """Serializer for producer's accept/reject response"""

    response_message = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text='Optional message to buyer'
    )
