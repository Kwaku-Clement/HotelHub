# utils.py
from django.utils import timezone
from .models import Reservation

def is_date_available(date):
    return not Reservation.objects.filter(reservation_date=date).exists()
