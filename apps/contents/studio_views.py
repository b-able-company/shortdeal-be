"""
Producer Studio API views for content management (CRUD)
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Count
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.core.response import success_response, error_response, paginated_response
from apps.core.permissions import IsProducer, IsOnboarded
from apps.core.constants import CONTENT_STATUS_PUBLIC, CONTENT_STATUS_DELETED
from .models import Content
from .serializers import ContentProducerSerializer, ContentCreateUpdateSerializer


@extend_schema(tags=['Studio - Content Management'])
class StudioContentListCreateView(APIView):
    """Producer's content list and create"""
    permission_classes = [IsProducer, IsOnboarded]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        responses={200: ContentProducerSerializer(many=True)}
    )
    def get(self, request):
        """List all contents from current producer"""
        queryset = Content.objects.filter(
            producer=request.user
        ).exclude(
            status=CONTENT_STATUS_DELETED
        ).annotate(
            offer_count=Count('offer')
        ).order_by('-created_at')

        # Status filter
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return paginated_response(
            queryset,
            ContentProducerSerializer,
            request,
            message="Contents retrieved successfully"
        )

    @extend_schema(
        request=ContentCreateUpdateSerializer,
        responses={
            201: ContentProducerSerializer,
            400: OpenApiResponse(description='Validation error')
        }
    )
    def post(self, request):
        """Create new content"""
        serializer = ContentCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            # Set producer to current user
            content = serializer.save(producer=request.user)
            response_serializer = ContentProducerSerializer(content)

            return success_response(
                data=response_serializer.data,
                message="Content created successfully",
                status_code=status.HTTP_201_CREATED
            )

        return error_response(
            message="Content creation failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(tags=['Studio - Content Management'])
class StudioContentDetailView(APIView):
    """Producer's content detail, update, delete"""
    permission_classes = [IsProducer, IsOnboarded]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, request, pk):
        """Get content owned by current producer"""
        try:
            return Content.objects.exclude(
                status=CONTENT_STATUS_DELETED
            ).get(pk=pk, producer=request.user)
        except Content.DoesNotExist:
            return None

    @extend_schema(
        responses={
            200: ContentProducerSerializer,
            404: OpenApiResponse(description='Content not found')
        }
    )
    def get(self, request, pk):
        """Get content detail"""
        content = self.get_object(request, pk)
        if not content:
            return error_response(
                message="Content not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = ContentProducerSerializer(content)
        return success_response(
            data=serializer.data,
            message="Content retrieved successfully"
        )

    @extend_schema(
        request=ContentCreateUpdateSerializer,
        responses={
            200: ContentProducerSerializer,
            400: OpenApiResponse(description='Validation error'),
            404: OpenApiResponse(description='Content not found')
        }
    )
    def patch(self, request, pk):
        """Update content"""
        content = self.get_object(request, pk)
        if not content:
            return error_response(
                message="Content not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = ContentCreateUpdateSerializer(
            content,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            response_serializer = ContentProducerSerializer(content)

            return success_response(
                data=response_serializer.data,
                message="Content updated successfully"
            )

        return error_response(
            message="Content update failed",
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        responses={
            200: OpenApiResponse(description='Content deleted'),
            404: OpenApiResponse(description='Content not found'),
            422: OpenApiResponse(description='Cannot delete - has offers')
        }
    )
    def delete(self, request, pk):
        """Soft delete content (only if no offers exist)"""
        content = self.get_object(request, pk)
        if not content:
            return error_response(
                message="Content not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Check if content has any offers
        offer_count = content.offer_set.count()
        if offer_count > 0:
            return error_response(
                message=f"Cannot delete content with {offer_count} existing offer(s)",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_code='CONTENT_HAS_OFFERS'
            )

        # Soft delete
        content.soft_delete()

        return success_response(
            message="Content deleted successfully"
        )


@extend_schema(tags=['Studio - Content Management'])
class StudioContentStatsView(APIView):
    """Producer's content statistics"""
    permission_classes = [IsProducer, IsOnboarded]

    @extend_schema(
        responses={200: OpenApiResponse(description='Content statistics')}
    )
    def get(self, request):
        """Get content statistics for current producer"""
        contents = Content.objects.filter(producer=request.user).exclude(
            status=CONTENT_STATUS_DELETED
        )

        stats = {
            'total_contents': contents.count(),
            'public_contents': contents.filter(status=CONTENT_STATUS_PUBLIC).count(),
            'draft_contents': contents.filter(status='draft').count(),
            'total_views': sum(c.view_count for c in contents),
            'total_offers': sum(c.offer_set.count() for c in contents),
        }

        return success_response(
            data=stats,
            message="Statistics retrieved successfully"
        )
