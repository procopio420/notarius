from django.http import HttpResponse


class PilotoLocalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Defense in addition to binding the server to loopback.
        if request.META.get('REMOTE_ADDR') not in ('127.0.0.1', '::1'):
            return HttpResponse(status=403)
        response = self.get_response(request)
        response['Cache-Control'] = 'no-store'
        return response
