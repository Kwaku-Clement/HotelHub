from django.db import models
from django.utils.timezone import now

class Guest(models.Model):
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, blank=True, null=True)
    address = models.TextField(max_length=256, blank=True, null=True)
    national_id = models.TextField(max_length=256, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    created_at = models.DateField(default=now)

    class Meta:
        db_table = 'Guests'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_select2(self):
        return {
            "label": self.get_full_name(),
            "value": self.id
        }
