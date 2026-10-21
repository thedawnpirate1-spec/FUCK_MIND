import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Central exception handler for Django REST Framework.
    Standardizes error messages and handles unhandled server errors as clean JSON.
    """
    response = exception_handler(exc, context)

    if response is not None:
        return response

    logger.error(f"Unexpected server error in endpoint: {exc}", exc_info=True)
    return Response(
        {"detail": "An internal server error occurred."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
