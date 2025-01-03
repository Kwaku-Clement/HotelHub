from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Guest
from django.core.cache import cache
from django.db.models import Q
from datetime import datetime, timedelta

@login_required(login_url="/authentication/login/")
def guests_list_view(request):
    cache_key = f'guest_list_{request.user.id}'
    cache.delete(cache_key)

    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_term = request.GET.get('search')

    guest_query = Guest.objects.all()

    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            end_date = end_date + timedelta(days=1)  # Include the end date
            guest_query = guest_query.filter(created_at__range=[start_date, end_date])
        except ValueError:
            pass

    if search_term:
        guest_query = guest_query.filter(
            Q(first_name__icontains=search_term) |
            Q(last_name__icontains=search_term) |
            Q(phone__icontains=search_term) |
            Q(national_id__icontains=search_term)
        )

    context = {
        "active_icon": "guests",
        "guests": guest_query,
        "start_date": start_date,
        "end_date": end_date,
        "search_term": search_term
    }
    return render(request, "guests.html", context=context)


@login_required(login_url="/authentication/login/")
def guests_add_view(request):
    context = {
        "active_icon": "guests",
    }

    if request.method == 'POST':
        data = request.POST
        attributes = {
            "first_name": data['first_name'],
            "last_name": data['last_name'],
            "address": data['address'],
            "national_id": data['national_id'],
            "phone": data['phone'],
        }

        if Guest.objects.filter(**attributes).exists():
            messages.error(request, 'Guest already exists!', extra_tags="warning")
            return redirect('guests:guests_add')

        try:
            new_guest = Guest.objects.create(**attributes)
            new_guest.save()
            messages.success(request, f'Guest: {attributes["first_name"]} {attributes["last_name"]} created successfully!', extra_tags="success")
            return redirect('guests:guests_list')
        except Exception as e:
            messages.error(request, 'There was an error during the creation!', extra_tags="danger")
            return redirect('guests:guests_add')

    return render(request, "guests_add.html", context=context)

@login_required(login_url="/authentication/login/")
def guests_update_view(request, guest_id):
    try:
        guest = Guest.objects.get(id=guest_id)
    except Exception as e:
        messages.error(request, 'There was an error trying to get the guest!', extra_tags="danger")
        return redirect('guests:guests_list')

    context = {
        "active_icon": "guests",
        "guest": guest,
    }

    if request.method == 'POST':
        data = request.POST
        attributes = {
            "first_name": data['first_name'],
            "last_name": data['last_name'],
            "address": data['address'],
            "national_id": data['national_id'],
            "phone": data['phone'],
        }

        if Guest.objects.filter(**attributes).exists():
            messages.error(request, 'Guest already exists!', extra_tags="warning")
            return redirect('guests:guests_add')

        try:
            guest = Guest.objects.get(id=guest_id)
            for key, value in attributes.items():
                setattr(guest, key, value)
            guest.save()
            messages.success(request, f'Guest: {guest.get_full_name()} updated successfully!', extra_tags="success")
            return redirect('guests:guests_list')
        except Exception as e:
            messages.error(request, 'There was an error during the update!', extra_tags="danger")
            return redirect('guests:guests_list')

    return render(request, "guests_update.html", context=context)


@login_required(login_url="/authentication/login/")
def guests_delete_view(request, guest_id):
    try:
        guest = Guest.objects.get(id=guest_id)
        guest.delete()
        messages.success(request, f'Guest: {guest.get_full_name()} deleted!', extra_tags="success")
        return redirect('guests:guests_list')
    except Exception as e:
        messages.error(request, 'There was an error during the deletion!', extra_tags="danger")
        return redirect('guests:guests_list')
