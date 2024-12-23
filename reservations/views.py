from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import get_template
from django.core.cache import cache
from datetime import datetime, timedelta, timezone
from weasyprint import HTML, CSS
from guests.models import Guest
from rooms.models import Room
from .models import Reservation, ReservationDetail
import json
import os
from django.utils.timezone import make_aware
from datetime import timezone


def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"

@login_required(login_url="authentication/login/")
def reservations_list_view(request):
    cache_key = f'reservations_list_{request.user.id}' 
    cache.delete(cache_key)
    
    reservations = (
        Reservation.objects.select_related('guest')
        .prefetch_related('reservationdetail_set__room')
        .filter(is_deleted=False) 
        .order_by('-id')[:100]
    )
    
    for reservation in reservations:
        reservation.status = reservation.get_status()
    
    context = {
        "active_icon": "reservations",
        "reservations": reservations,
    }
    return render(request, "reservations.html", context=context)


@login_required(login_url="authentication/login/")
def reservations_add_view(request, reservation_id=None):
    context = {
        "active_icon": "reservations",
        "guests": [
            g.to_select2() for g in Guest.objects.only("id", "first_name", "last_name")
        ],
    }

    if request.method == "POST" and request.content_type == "application/json":
        try:
            data = json.loads(request.body)

            # Convert check-in and check-out to UTC
            naive_check_in = datetime.strptime(data["check_in"], "%Y-%m-%d")
            naive_check_out = datetime.strptime(data["check_out"], "%Y-%m-%d")
            check_in = make_aware(naive_check_in)
            check_out = make_aware(naive_check_out)

            # Get guest
            guest = Guest.objects.get(id=int(data["guest"]))

            # Check room availability
            requested_room_ids = [int(room["id"]) for room in data["rooms"]]
            existing_reservations = Reservation.objects.filter(
                Q(check_in__lt=check_out) &
                Q(check_out__gt=check_in),
                reservationdetail__room_id__in=requested_room_ids
            ).distinct()

            if existing_reservations.exists():
                return JsonResponse({
                    "status": "error",
                    "message": "The selected room is not available for the selected dates."
                }, status=400)

            # Create reservation
            reservation = Reservation.objects.create(
                guest=guest,
                sub_total=float(data["sub_total"]),
                grand_total=float(data["grand_total"]),
                tax_amount=float(data["tax_amount"]),
                tax_percentage=float(data["tax_percentage"]),
                amount_payed=float(data["amount_payed"]),
                amount_change=float(data["amount_change"]),
                reservation_date=data["reservation_date"],
                check_in=check_in,
                check_out=check_out,
                status="Reserved",
                created_by=request.user
            )
            # Create reservation details
            for room_data in data["rooms"]:
                room = Room.objects.get(id=int(room_data["id"]))
                ReservationDetail.objects.create(
                    reservation=reservation,
                    room=room,
                    price=float(room_data["price"]),
                    days=int(room_data["days"]),
                    total_detail=float(room_data["total_room"])
                )

            return JsonResponse({"status": "success"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return render(request, "reservations_add.html", context=context)


@login_required(login_url="authentication/login/")
def reservations_details_view(request, reservation_id):
    reservation = get_object_or_404(Reservation.objects.select_related("guest"), id=reservation_id)
    context = {
        "active_icon": "reservations",
        "reservation": reservation,
        "details": ReservationDetail.objects.filter(reservation=reservation),
    }
    return render(request, "reservations_details.html", context=context)

@login_required(login_url="authentication/login/")
def receipt_pdf_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    template = get_template("reservations_receipt_pdf.html")
    css_url = os.path.join(settings.BASE_DIR, "static/css/receipt_pdf/bootstrap.min.css")
    html_content = template.render(
        {
            "reservation": reservation,
            "details": ReservationDetail.objects.filter(reservation=reservation),
        }
    )

    cache_key = f"pdf_receipt_{reservation_id}"
    pdf = cache.get(cache_key)
    if not pdf:
        pdf = HTML(string=html_content).write_pdf(stylesheets=[CSS(css_url)])
        cache.set(cache_key, pdf, timeout=3600)

    return HttpResponse(pdf, content_type="application/pdf")

@login_required(login_url="authentication/login/")
def reservations_report_view(request):
    time_filter = request.GET.get("filter", "custom")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    today = datetime.today().date()

    time_ranges = {
        "daily": (today, today),
        "weekly": (today - timedelta(days=7), today),
        "monthly": (today.replace(day=1), today),
        "yearly": (today.replace(month=1, day=1), today),
        "custom": (
            datetime.strptime(start_date, "%Y-%m-%d") if start_date else None,
            datetime.strptime(end_date, "%Y-%m-%d") if end_date else None,
        ),
    }
    start_date, end_date = time_ranges.get(time_filter, (None, None))

    # If no date range is selected, return an empty list of reservations
    if not start_date or not end_date:
        reservations = []
    else:
        cache_key = f"reservations_report_{time_filter}_{start_date}_{end_date}"
        reservations = cache.get(cache_key)
        if not reservations:
            reservations = list(
                Reservation.objects.prefetch_related('reservationdetail_set__room')
                .select_related('guest')
                .filter(reservation_date__range=(start_date, end_date))
            )
            cache.set(cache_key, reservations, timeout=3600)

    # Calculate grand total and number of days for each reservation
    grand_total = sum(r.grand_total for r in reservations)
    for r in reservations:
        r.days_spent = (r.check_out - r.check_in).days

    context = {
        "active_icon": "report",
        "reservations": reservations,
        "time_filter": time_filter,
        "start_date": start_date,
        "end_date": end_date,
        "grand_total": grand_total,
    }
    return render(request, "reservations_report.html", context=context)

@login_required(login_url="authentication/login/")
def update_reservation_status_view(request, reservation_id, status):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    valid_statuses = ["check_in", "check_out", "cancel"]
    if status not in valid_statuses:
        return JsonResponse({"status": "error", "message": "Invalid status"}, status=400)

    if status == "check_in":
        reservation.status = "Checked In"
        reservation.check_in = timezone.now()
    elif status == "check_out":
        reservation.status = "Checked Out"
        reservation.check_out = timezone.now()
    elif status == "cancel":
        reservation.status = "Canceled"

    reservation.save()

    messages.success(request, f"Reservation marked as {reservation.status}.")
    return JsonResponse({"status": "success", "reservation_status": reservation.status}, status=200)


@login_required(login_url="authentication/login/")
@permission_required('reservations.delete_reservation', raise_exception=True)
def reservations_delete(request, id):
    reservation = get_object_or_404(Reservation, id=id)
    if request.method == 'POST':
        reservation.delete()
        
        # Clear all related caches
        cache.delete_many([
            f'reservations_list_{request.user.id}',
            f'reservation_details_{id}',
            f'pdf_receipt_{id}'
        ])
        
        messages.success(request, 'Reservation deleted successfully.')
        return redirect('reservations:reservations_list')
    return HttpResponseNotAllowed(['POST'])