from django.conf import settings
from django.db import models
from django.utils.timezone import now
from guests.models import Guest
from rooms.models import Room

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Checked In', 'Checked In'),
        ('Checked Out', 'Checked Out'),
        ('Canceled', 'Canceled'),
    ]
    
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='deleted_reservations'
    )

    reservation_date = models.DateField(default=now)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    tax_percentage = models.FloatField(default=0)
    amount_payed = models.FloatField(default=0)
    amount_change = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = "Reservations"

    def __str__(self):
        return f"Reservation {self.id}: {self.guest} on {self.reservation_date}"

    def sum_items(self):
        details = ReservationDetail.objects.filter(reservation=self)
        return sum([d.days for d in details])

    def get_status(self):
        current_date = now()
        if self.check_in and self.check_out:
            if current_date < self.check_in:
                return 'Pending'
            elif current_date >= self.check_in and current_date <= self.check_out:
                return 'Active'
            elif current_date > self.check_out:
                return 'Inactive'
        return self.status

class ReservationDetail(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    price = models.FloatField()
    total_detail = models.FloatField()
    days = models.IntegerField(default=1)

    def __str__(self):
        return f"Detail {self.id}: {self.room} in {self.reservation} for {self.days} days"
