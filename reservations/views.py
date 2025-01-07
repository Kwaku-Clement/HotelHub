from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import get_template
from django.core.cache import cache
from datetime import datetime, timedelta, timezone
from activitylog.models import ActivityLog
from activitylog.views import get_mac_address
from guests.models import Guest
from rooms.models import Room
from .models import Reservation, ReservationDetail
import json
import os
from django.utils.timezone import make_aware
from datetime import timezone
from xhtml2pdf import pisa

def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"

@login_required(login_url="/authentication/login/")
def reservations_list_view(request):
    cache_key = f'reservations_list_{request.user.id}'
    cache.delete(cache_key)

    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    reservations_query = (
        Reservation.objects.select_related('guest')
        .prefetch_related('reservationdetail_set__room')
        .filter(is_deleted=False)
    )

    # Apply date filtering if provided
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = end_date + timedelta(days=1)  # Include the end date

            reservations_query = reservations_query.filter(
                reservation_date__range=[start_date, end_date]
            )
        except ValueError:
            pass  # Invalid date format, ignore filtering

    reservations = reservations_query.order_by('-id')[:100]

    for reservation in reservations:
        reservation.status = reservation.get_status()

    context = {
        "active_icon": "reservations",
        "reservations": reservations,
    }

    # Log activity
    if request.user.is_authenticated:
        action = f"Viewed reservations list"
        details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
        ip_address = request.META.get('REMOTE_ADDR')
        mac_address = get_mac_address()
        ActivityLog.objects.create(
            user=request.user,
            action=action,
            details=details,
            ip_address=ip_address,
            mac_address=mac_address
        )

    return render(request, "reservations.html", context=context)


@login_required(login_url="/authentication/login/")
def reservations_add_create_view(request, reservation_id=None):
    context = {
        "active_icon": "reservations",
        "guests": [
            g.to_select2() for g in Guest.objects.only("id", "first_name", "last_name")
        ],
    }

    if reservation_id:
        reservation = get_object_or_404(Reservation, id=reservation_id)
        context['reservation'] = reservation
        context['reservation_details'] = reservation.reservationdetail_set.all()
        context['amount_payed'] = reservation.amount_payed
        
    if request.method == "POST":
        if request.content_type == "application/json":
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
                ).exclude(id=reservation_id).distinct()

                if existing_reservations.exists():
                    return JsonResponse({
                        "status": "error",
                        "message": "The selected room is not available for the selected dates."
                    }, status=400)

                # Create or update reservation
                if reservation_id:
                    reservation = Reservation.objects.get(id=reservation_id)
                    reservation.guest = guest
                    reservation.sub_total = float(data["sub_total"])
                    reservation.grand_total = float(data["grand_total"])
                    reservation.tax_amount = float(data["tax_amount"])
                    reservation.tax_percentage = float(data["tax_percentage"])
                    reservation.amount_paid = float(data["amount_paid"])
                    reservation.amount_change = float(data["amount_change"])
                    reservation.check_in = check_in
                    reservation.check_out = check_out
                    reservation.save()

                    # Delete existing reservation details
                    reservation.reservationdetail_set.all().delete()
                else:
                    reservation = Reservation.objects.create(
                        guest=guest,
                        sub_total=float(data["sub_total"]),
                        grand_total=float(data["grand_total"]),
                        tax_amount=float(data["tax_amount"]),
                        tax_percentage=float(data["tax_percentage"]),
                        amount_paid=float(data["amount_paid"]),
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

                # Log activity
                action = f"{'Updated' if reservation_id else 'Created'} reservation: {reservation.id}"
                details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
                ip_address = request.META.get('REMOTE_ADDR')
                mac_address = get_mac_address()
                ActivityLog.objects.create(
                    user=request.user,
                    action=action,
                    details=details,
                    ip_address=ip_address,
                    mac_address=mac_address
                )

                return JsonResponse({"status": "success"})

            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            # Handle non-JSON POST requests (e.g., status updates)
            if reservation_id:
                reservation = get_object_or_404(Reservation, id=reservation_id)
                valid_statuses = ["check_in", "check_out", "cancel"]
                status = request.POST.get('status')
                if status and status in valid_statuses:
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

                    # Log activity
                    action = f"Updated reservation status to: {reservation.status} for reservation: {reservation.id}"
                    details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
                    ip_address = request.META.get('REMOTE_ADDR')
                    mac_address = get_mac_address()
                    ActivityLog.objects.create(
                        user=request.user,
                        action=action,
                        details=details,
                        ip_address=ip_address,
                        mac_address=mac_address
                    )

                    return JsonResponse({"status": "success", "reservation_status": reservation.status}, status=200)

    return render(request, "reservations_add.html", context=context)

@login_required(login_url="/authentication/login/")
def reservations_details_view(request, reservation_id):
    reservation = get_object_or_404(Reservation.objects.select_related("guest"), id=reservation_id)
    context = {
        "active_icon": "reservations",
        "reservation": reservation,
        "details": ReservationDetail.objects.filter(reservation=reservation),
    }

    # Log activity
    if request.user.is_authenticated:
        action = f"Viewed reservation details: {reservation.id}"
        details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
        ip_address = request.META.get('REMOTE_ADDR')
        mac_address = get_mac_address()
        ActivityLog.objects.create(
            user=request.user,
            action=action,
            details=details,
            ip_address=ip_address,
            mac_address=mac_address
        )

    return render(request, "reservations_details.html", context=context)

@login_required(login_url="/authentication/login/")
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
        response = HttpResponse(content_type="application/pdf")
        pisa.pisaDocument(html_content, response, link_callback=fetch_resources)
        pdf = response.content
        cache.set(cache_key, pdf, timeout=3600)

    # Log activity
    if request.user.is_authenticated:
        action = f"Generated PDF receipt for reservation: {reservation.id}"
        details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
        ip_address = request.META.get('REMOTE_ADDR')
        mac_address = get_mac_address()
        ActivityLog.objects.create(
            user=request.user,
            action=action,
            details=details,
            ip_address=ip_address,
            mac_address=mac_address
        )

    return HttpResponse(pdf, content_type="application/pdf")

def fetch_resources(uri, rel):
    """
    Callback to allow xhtml2pdf/reportlab to retrieve Images,Stylesheets, etc.
    `uri` is the href attribute from the html link element.
    `rel` gives a relative path, but it's not used here.
    """
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:
        path = os.path.join(settings.BASE_DIR, uri)

    return path

@login_required(login_url="/authentication/login/")
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

        # Log activity
        action = f"Deleted reservation: {reservation.id}"
        details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
        ip_address = request.META.get('REMOTE_ADDR')
        mac_address = get_mac_address()
        ActivityLog.objects.create(
            user=request.user,
            action=action,
            details=details,
            ip_address=ip_address,
            mac_address=mac_address
        )

        return redirect('reservations:reservations_list')
    return HttpResponseNotAllowed(['POST'])
