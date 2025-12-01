"""
Response envelope helpers for consistent API responses
"""
from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK, **kwargs):
    """
    Standard success response envelope
    {success: true, data: {...}, message: "..."}
    """
    response_data = {
        'success': True,
        'data': data,
        'message': message,
    }

    # Add optional fields (pagination, meta, etc.)
    response_data.update(kwargs)

    return Response(response_data, status=status_code)


def error_response(message="Error occurred", errors=None, error_code=None, status_code=status.HTTP_400_BAD_REQUEST, **kwargs):
    """
    Standard error response envelope
    {success: false, data: null, message: "...", errors: {...}, error: {code: "...", message: "..."}}
    """
    response_data = {
        'success': False,
        'data': None,
        'message': message,
    }

    if errors:
        response_data['errors'] = errors

    if error_code:
        response_data['error'] = {
            'code': error_code,
            'message': message
        }

    # Add optional fields
    response_data.update(kwargs)

    return Response(response_data, status=status_code)


def paginated_response(queryset, serializer_class, request, message="Success"):
    """
    Helper for paginated responses
    """
    from rest_framework.pagination import PageNumberPagination

    paginator = PageNumberPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(paginated_queryset, many=True)

    return success_response(
        data=serializer.data,
        message=message,
        pagination={
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'page_size': paginator.page_size,
            'current_page': paginator.page.number,
            'total_pages': paginator.page.paginator.num_pages,
        }
    )
