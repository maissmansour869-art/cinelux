from dataclasses import dataclass

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


@dataclass
class CineLuxError(Exception):
    error_code: str
    message: str
    http_status: int = status.HTTP_400_BAD_REQUEST
    details: object | None = None


ERROR_STATUS = {
    "GEN-400": 400, "GEN-401": 401, "GEN-403": 403, "GEN-404": 404, "GEN-500": 500,
    "AUTH-001": 401, "AUTH-002": 409, "AUTH-003": 403,
    "MOV-404": 404, "SHOW-404": 404, "SHOW-409": 409,
    "SEAT-404": 404, "SEAT-409": 409,
    "BOOK-404": 404, "BOOK-403": 403, "BOOK-410": 410, "BOOK-422": 422,
    "PAY-402": 402, "PAY-503": 503,
    "VAL-400": 400, "VAL-401": 400, "VAL-403": 403, "VAL-409": 409, "VAL-410": 425, "VAL-411": 410,
    "ADM-409": 409,
}


def error_response(error_code, message, *, details=None, request=None, http_status=None):
    body = {"errorCode": error_code, "message": message, "traceId": getattr(request, "trace_id", None)}
    if details is not None:
        body["details"] = details
    return Response(body, status=http_status or ERROR_STATUS.get(error_code, 400))


def exception_handler(exc, context):
    request = context.get("request")
    if isinstance(exc, CineLuxError):
        return error_response(exc.error_code, exc.message, details=exc.details, request=request, http_status=exc.http_status)
    response = drf_exception_handler(exc, context)
    if response is None:
        return error_response("GEN-500", "Unhandled server error.", request=request, http_status=500)
    code = "GEN-401" if response.status_code == 401 else "GEN-403" if response.status_code == 403 else "GEN-400"
    response.data = {
        "errorCode": code,
        "message": response.data.get("detail", "Request failed.") if isinstance(response.data, dict) else "Request failed.",
        "traceId": getattr(request, "trace_id", None),
    }
    return response
