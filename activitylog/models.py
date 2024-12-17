from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models

class ActivityLog(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    deleted_item = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'activity_log'
        ordering = ['-timestamp']
        permissions = [
            ("view_activity_log", "Can view activity log"),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"
