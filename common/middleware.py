import uuid


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.trace_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        response = self.get_response(request)
        response["X-Request-ID"] = request.trace_id
        return response
