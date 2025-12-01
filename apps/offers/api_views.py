"""
API views for Offer management
"""
from rest_framework import status
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.core.response import success_response, error_response, paginated_response
from apps.core.permissions import IsBuyer, IsOnboarded
from apps.core.constants import OFFER_STATUS_PENDING
from .models import Offer
from .serializers import OfferBuyerSerializer, OfferProducerSerializer, OfferResponseSerializer


@extend_schema(tags=['Offers - Buyer'])
class BuyerOfferListCreateView(APIView):
    """Buyer's offer list and create"""
    permission_classes = [IsBuyer, IsOnboarded]

    @extend_schema(responses={200: OfferBuyerSerializer(many=True)})
    def get(self, request):
        """List all offers from current buyer"""
        queryset = Offer.objects.filter(buyer=request.user).select_related(
            'content', 'content__producer'
        ).order_by('-created_at')

        # Status filter
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return paginated_response(
            queryset,
            OfferBuyerSerializer,
            request,
            message="Offers retrieved successfully"
        )

    @extend_schema(
        request=OfferBuyerSerializer,
        responses={201: OfferBuyerSerializer, 400: OpenApiResponse(description='Validation error')}
    )
    def post(self, request):
        """Create new offer"""
        serializer = OfferBuyerSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            offer = serializer.save(buyer=request.user)
            return success_response(
                data=OfferBuyerSerializer(offer).data,
                message="Offer created successfully",
                status_code=status.HTTP_201_CREATED
            )

        return error_response(
            message="Offer creation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(tags=['Offers - Buyer'])
class BuyerOfferDetailView(APIView):
    """Buyer's offer detail"""
    permission_classes = [IsBuyer, IsOnboarded]

    @extend_schema(responses={200: OfferBuyerSerializer, 404: OpenApiResponse(description='Not found')})
    def get(self, request, pk):
        """Get offer detail"""
        try:
            offer = Offer.objects.select_related('content', 'content__producer').get(pk=pk, buyer=request.user)
        except Offer.DoesNotExist:
            return error_response(message="Offer not found", status_code=status.HTTP_404_NOT_FOUND)

        return success_response(
            data=OfferBuyerSerializer(offer).data,
            message="Offer retrieved successfully"
        )


@extend_schema(tags=['Offers - Producer'])
class ProducerOfferListView(APIView):
    """Producer's offer list"""
    permission_classes = [IsOnboarded]

    @extend_schema(responses={200: OfferProducerSerializer(many=True)})
    def get(self, request):
        """List all offers for producer's contents"""
        queryset = Offer.objects.filter(
            content__producer=request.user
        ).select_related('buyer', 'content').order_by('-created_at')

        # Status filter
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return paginated_response(
            queryset,
            OfferProducerSerializer,
            request,
            message="Offers retrieved successfully"
        )


@extend_schema(tags=['Offers - Producer'])
class ProducerOfferDetailView(APIView):
    """Producer's offer detail"""
    permission_classes = [IsOnboarded]

    @extend_schema(responses={200: OfferProducerSerializer, 404: OpenApiResponse(description='Not found')})
    def get(self, request, pk):
        """Get offer detail"""
        try:
            offer = Offer.objects.select_related('buyer', 'content').get(pk=pk, content__producer=request.user)
        except Offer.DoesNotExist:
            return error_response(message="Offer not found", status_code=status.HTTP_404_NOT_FOUND)

        return success_response(
            data=OfferProducerSerializer(offer).data,
            message="Offer retrieved successfully"
        )


@extend_schema(tags=['Offers - Producer'])
class ProducerOfferAcceptView(APIView):
    """Producer accept offer"""
    permission_classes = [IsOnboarded]

    @extend_schema(
        request=OfferResponseSerializer,
        responses={200: OfferProducerSerializer, 400: OpenApiResponse(description='Cannot accept')}
    )
    def post(self, request, pk):
        """Accept offer"""
        try:
            offer = Offer.objects.get(pk=pk, content__producer=request.user)
        except Offer.DoesNotExist:
            return error_response(message="Offer not found", status_code=status.HTTP_404_NOT_FOUND)

        try:
            response_msg = request.data.get('response_message', '')
            offer.accept(producer_response=response_msg)

            return success_response(
                data=OfferProducerSerializer(offer).data,
                message="Offer accepted successfully"
            )
        except ValueError as e:
            return error_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Offers - Producer'])
class ProducerOfferRejectView(APIView):
    """Producer reject offer"""
    permission_classes = [IsOnboarded]

    @extend_schema(
        request=OfferResponseSerializer,
        responses={200: OfferProducerSerializer, 400: OpenApiResponse(description='Cannot reject')}
    )
    def post(self, request, pk):
        """Reject offer"""
        try:
            offer = Offer.objects.get(pk=pk, content__producer=request.user)
        except Offer.DoesNotExist:
            return error_response(message="Offer not found", status_code=status.HTTP_404_NOT_FOUND)

        try:
            response_msg = request.data.get('response_message', '')
            offer.reject(producer_response=response_msg)

            return success_response(
                data=OfferProducerSerializer(offer).data,
                message="Offer rejected successfully"
            )
        except ValueError as e:
            return error_response(message=str(e), status_code=status.HTTP_400_BAD_REQUEST)
