"""
API views for LOI management
"""
from django.http import FileResponse
from rest_framework import status
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.core.response import success_response, error_response, paginated_response
from apps.core.permissions import IsRelatedParty
from .models import LOI
from .serializers import LOISerializer


@extend_schema(tags=['LOI'])
class LOIListView(APIView):
    """List LOIs for current user (buyer or producer)"""
    permission_classes = [IsRelatedParty]

    @extend_schema(responses={200: LOISerializer(many=True)})
    def get(self, request):
        """List all LOIs where user is buyer or producer"""
        queryset = LOI.objects.filter(
            buyer=request.user
        ) | LOI.objects.filter(
            producer=request.user
        )
        queryset = queryset.select_related('buyer', 'producer', 'offer').order_by('-created_at')

        return paginated_response(
            queryset,
            LOISerializer,
            request,
            message="LOIs retrieved successfully"
        )


@extend_schema(tags=['LOI'])
class LOIDetailView(APIView):
    """LOI detail view (accessible only by related parties)"""

    @extend_schema(
        responses={
            200: LOISerializer,
            403: OpenApiResponse(description='Not authorized'),
            404: OpenApiResponse(description='Not found')
        }
    )
    def get(self, request, pk):
        """Get LOI detail"""
        try:
            loi = LOI.objects.select_related('buyer', 'producer', 'offer').get(pk=pk)
        except LOI.DoesNotExist:
            return error_response(message="LOI not found", status_code=status.HTTP_404_NOT_FOUND)

        # Check if user is related party (buyer or producer)
        if request.user != loi.buyer and request.user != loi.producer:
            return error_response(
                message="You are not authorized to view this LOI",
                status_code=status.HTTP_403_FORBIDDEN
            )

        return success_response(
            data=LOISerializer(loi).data,
            message="LOI retrieved successfully"
        )


@extend_schema(tags=['LOI'])
class LOIPDFDownloadView(APIView):
    """Download LOI PDF (accessible only by related parties)"""

    @extend_schema(
        responses={
            200: OpenApiResponse(description='PDF file'),
            403: OpenApiResponse(description='Not authorized'),
            404: OpenApiResponse(description='Not found'),
            503: OpenApiResponse(description='PDF generating')
        }
    )
    def get(self, request, pk):
        """Download LOI PDF"""
        try:
            loi = LOI.objects.select_related('buyer', 'producer', 'offer').get(pk=pk)
        except LOI.DoesNotExist:
            return error_response(message="LOI not found", status_code=status.HTTP_404_NOT_FOUND)

        # Check if user is related party (buyer or producer)
        if request.user != loi.buyer and request.user != loi.producer:
            return error_response(
                message="You are not authorized to download this LOI PDF",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Check if PDF is ready
        if not loi.is_pdf_ready:
            return error_response(
                message="PDF is being generated. Please try again in a few moments.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                error_code='PDF_GENERATING'
            )

        # Return PDF file
        response = FileResponse(
            loi.pdf_file.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{loi.document_number}.pdf"'
        return response
