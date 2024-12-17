from django.db import models
from django.utils import timezone
from django.conf import settings

class Miscellaneous(models.Model):
    EXPENSE_TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('maintenance', 'Maintenance'),
        ('servicing', 'Servicing'),
        ('other', 'Other'),
    ]

    type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='other')
    description = models.TextField(max_length=256)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "Miscellaneous"
        verbose_name_plural = "Miscellaneous Expenses"

    def __str__(self):
        return f"{self.get_type_display()} - {self.date.strftime('%Y-%m-%d')}"

    def to_json(self):
        return {
            'id': self.id,
            'type': self.get_type_display(),
            'description': self.description,
            'amount': float(self.amount),
            'date': self.date.strftime('%Y-%m-%d'),
            'created_by': self.created_by.get_full_name() if self.created_by else 'Unknown'
        }
