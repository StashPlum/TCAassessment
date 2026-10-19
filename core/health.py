"""Plain health check for the hosting platform.

Answered before host validation and the HTTPS redirect, because the platform probes the app over its
internal address with plain HTTP. It returns no data and touches no records.
"""
from django.http import HttpResponse

class HealthCheckMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        if request.path_info=='/healthz/': return HttpResponse('ok',content_type='text/plain')
        return self.get_response(request)
