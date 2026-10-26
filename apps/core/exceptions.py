import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger("brofessor")


def custom_exception_handler(exc, context):
    """
    Standardized DRF Exception Handler.
    Ensures all API errors return a consistent envelope:
    {
        "success": false,
        "error": {
            "status_code": 400,
            "type": "ValidationError",
            "message": "Human readable message",
            "details": {...}
        }
    }
    """
    # Call REST framework's default exception handler first to get the standard error response.
    response = exception_handler(exc, context)

    # Now add our uniform error envelope
    if response is not None:
        view_name = context.get("view", None)
        view_str = view_name.__class__.__name__ if view_name else "UnknownView"

        error_payload = {
            "success": False,
            "error": {
                "status_code": response.status_code,
                "type": exc.__class__.__name__,
                "message": getattr(exc, "detail", str(exc)) if not isinstance(getattr(exc, "detail", None), (dict, list)) else "Validation or processing error occurred.",
                "details": response.data,
            },
        }

        logger.warning(
            f"API Error in {view_str}: {exc.__class__.__name__} - {response.status_code}"
        )
        response.data = error_payload
        return response

    # Unhandled exceptions (e.g. 500 Internal Server Error)
    logger.exception(f"Unhandled Exception in API: {str(exc)}", exc_info=exc)
    return Response(
        {
            "success": False,
            "error": {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "type": "InternalServerError",
                "message": "An unexpected server error occurred.",
                "details": str(exc),
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
