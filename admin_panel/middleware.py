from django.http import HttpResponseForbidden
from django.conf import settings


class AdminIPRestrictionMiddleware:
    """
    Blocks access to the admin portal from any IP not listed in
    settings.ADMIN_ALLOWED_IPS.

    HOW TO ADD IPs:
      - In development: edit ADMIN_ALLOWED_IPS in settings.py
      - In production:  set the environment variable:
            ADMIN_ALLOWED_IPS=203.0.113.5,198.51.100.8
        (comma-separated, no spaces)

    HOW TO FIND YOUR IP:
      - Visit https://www.whatismyip.com/ to get your current public IP.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_prefix = getattr(settings, 'ADMIN_SECRET_PREFIX', 'sv-cd6n-lugl')

    def __call__(self, request):
        # Only apply restriction to the admin portal URL prefix
        if request.path.startswith(f'/{self.admin_prefix}/'):
            allowed_ips = getattr(settings, 'ADMIN_ALLOWED_IPS', ['127.0.0.1', '::1'])

            # Support X-Forwarded-For header (when behind a proxy/load balancer)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                client_ip = x_forwarded_for.split(',')[0].strip()
            else:
                client_ip = request.META.get('REMOTE_ADDR', '')

            if client_ip not in allowed_ips:
                return HttpResponseForbidden(
                    '<h1>403 Forbidden</h1>'
                    '<p>Access to this resource is restricted.</p>'
                )

        return self.get_response(request)
