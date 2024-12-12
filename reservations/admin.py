from django.contrib import admin

from .models import Reservation, ReservationDetail

admin.site.register(Reservation)
admin.site.register(ReservationDetail)
