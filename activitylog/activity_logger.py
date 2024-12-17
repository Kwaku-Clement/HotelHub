from django.utils import timezone
from .models import ActivityLog
import uuid

class ActivityLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            action = f"{request.method} {request.path}"
            details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
            ip_address = request.META.get('REMOTE_ADDR')
            mac_address = self.get_mac_address()
            ActivityLog.objects.create(user=request.user, action=action, details=details, ip_address=ip_address, mac_address=mac_address)
        return response

    def get_mac_address(self):
        mac_num = hex(uuid.getnode()).replace('0x', '').upper()
        mac = '-'.join(mac_num[i: i+2] for i in range(0, 11, 2))
        return mac
