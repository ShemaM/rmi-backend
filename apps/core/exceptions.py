"""Consistent error envelope so the Next.js client handles every error the same way:

{"error": {"code": "not_found", "message": "Not found.", "details": {...}}}
"""

from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None  # unhandled -> Django 500, logged

    data = response.data
    code = getattr(exc, "default_code", "error")

    if isinstance(data, dict) and set(data) == {"detail"}:
        message, details = str(data["detail"]), None
    else:
        message, details = "Invalid input.", data
        code = "validation_error" if response.status_code == 400 else code

    response.data = {"error": {"code": code, "message": message, "details": details}}
    return response
