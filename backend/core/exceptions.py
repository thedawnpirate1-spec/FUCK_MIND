import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Zentraler Exception Handler für Django REST Framework.
    Standardisiert Fehlermeldungen und fängt unbehandelte Serverfehler als sauberes JSON ab.
    """
    response = exception_handler(exc, context)

    if response is not None:
        return response

    logger.error(f"Unerwarteter Serverfehler im Endpunkt: {exc}", exc_info=True)
    return Response(
        {"detail": "Ein interner Serverfehler ist aufgetreten."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
