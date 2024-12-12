from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Guest

@login_required(login_url="/authentication/login/")
def guests_list_view(request):
    context = {
        "active_icon": "guests",
        "guests": Guest.objects.all()
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
