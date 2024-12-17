from .models import ActivityLog
import uuid
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from .models import ActivityLog

@permission_required('activitylog.view_activity_log', raise_exception=True)
def activity_log_view(request):
    logs = ActivityLog.objects.all()
    context = {
        "logs": logs
    }
    return render(request, "activity_log.html", context)

def get_mac_address():
    mac_num = hex(uuid.getnode()).replace('0x', '').upper()
    mac = '-'.join(mac_num[i: i+2] for i in range(0, 11, 2))
    return mac
