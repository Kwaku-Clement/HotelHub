from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from activitylog.models import ActivityLog
from activitylog.views import get_mac_address
from .models import RoomType, Room


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

@login_required(login_url="/authentication/login/")
def room_types_list_view(request):
    context = {
        "active_icon": "room_types",
        "room_types": RoomType.objects.all()
    }

    # Log activity
    if request.user.is_authenticated:
        action = f"Viewed room types list"
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

    return render(request, "room_types.html", context=context)

@login_required(login_url="/authentication/login/")
def room_types_add_view(request):
    context = {
        "active_icon": "room_types",
        "room_type_status": RoomType.status.field.choices
    }

    if request.method == 'POST':
        data = request.POST
        attributes = {
            "name": data['name'],
            "status": data['state'],
            "description": data['description']
        }

        if RoomType.objects.filter(**attributes).exists():
            messages.error(request, 'Room type already exists!', extra_tags="warning")
            return redirect('rooms:room_types_add')

        try:
            new_room_type = RoomType.objects.create(**attributes)
            new_room_type.save()
            messages.success(request, f'Room type: {attributes["name"]} created successfully!', extra_tags="success")

            # Log activity
            action = f"Created room type: {attributes['name']}"
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

            return redirect('rooms:room_types_list')
        except Exception as e:
            messages.error(request, 'There was an error during the creation!', extra_tags="danger")
            return redirect('rooms:room_types_add')

    return render(request, "room_types_add.html", context=context)

@login_required(login_url="/authentication/login/")
def room_types_update_view(request, room_type_id):
    try:
        room_type = RoomType.objects.get(id=room_type_id)
    except Exception as e:
        messages.error(request, 'There was an error trying to get the room type!', extra_tags="danger")
        return redirect('rooms:room_types_list')

    context = {
        "active_icon": "room_types",
        "room_type_status": RoomType.status.field.choices,
        "room_type": room_type
    }

    if request.method == 'POST':
        data = request.POST
        attributes = {
            "name": data['name'],
            "status": data['state'],
            "description": data['description']
        }

        if RoomType.objects.filter(**attributes).exists():
            messages.error(request, 'Room type already exists!', extra_tags="warning")
            return redirect('rooms:room_types_add')

        try:
            room_type = RoomType.objects.filter(id=room_type_id).update(**attributes)
            room_type = RoomType.objects.get(id=room_type_id)
            messages.success(request, f'Room type: {room_type.name} updated successfully!', extra_tags="success")

            # Log activity
            action = f"Updated room type: {room_type.name}"
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

            return redirect('rooms:room_types_list')
        except Exception as e:
            messages.error(request, 'There was an error during the update!', extra_tags="danger")
            return redirect('rooms:room_types_list')

    return render(request, "room_types_update.html", context=context)

@login_required(login_url="/authentication/login/")
def room_types_delete_view(request, room_type_id):
    try:
        room_type = RoomType.objects.get(id=room_type_id)
        room_type.delete()
        messages.success(request, f'Room type: {room_type.name} deleted!', extra_tags="success")

        # Log activity
        action = f"Deleted room type: {room_type.name}"
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

        return redirect('rooms:room_types_list')
    except Exception as e:
        messages.error(request, 'There was an error during the deletion!', extra_tags="danger")
        return redirect('rooms:room_types_list')

@login_required(login_url="/authentication/login/")
def rooms_list_view(request):
    context = {
        "active_icon": "rooms",
        "rooms": Room.objects.all()
    }

    # Log activity
    if request.user.is_authenticated:
        action = f"Viewed rooms list"
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

    return render(request, "rooms.html", context=context)

@login_required(login_url="/authentication/login/")
def rooms_add_view(request):
    context = {
        "active_icon": "room_types",
        "room_status": Room.status.field.choices,
        "room_types": RoomType.objects.all().filter(status="ACTIVE")
    }

    if request.method == 'POST':
        data = request.POST
        attributes = {
            "name": data['name'],
            "status": data['state'],
            "description": data['description'],
            "room_type": RoomType.objects.get(id=data['room_type']),
            "price": data['price']
        }

        if Room.objects.filter(**attributes).exists():
            messages.error(request, 'Room already exists!', extra_tags="warning")
            return redirect('rooms:rooms_add')

        try:
            new_room = Room.objects.create(**attributes)
            new_room.save()
            messages.success(request, f'Room: {attributes["name"]} created successfully!', extra_tags="success")

            # Log activity
            action = f"Created room: {attributes['name']}"
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

            return redirect('rooms:rooms_list')
        except Exception as e:
            messages.error(request, 'There was an error during the creation!', extra_tags="danger")
            return redirect('rooms:rooms_add')

    return render(request, "rooms_add.html", context=context)

@login_required(login_url="/authentication/login/")
def rooms_update_view(request, room_id):
    try:
        room = Room.objects.get(id=room_id)
    except Exception as e:
        messages.error(request, 'There was an error trying to get the room!', extra_tags="danger")
        return redirect('rooms:rooms_list')

    context = {
        "active_icon": "rooms",
        "room_status": Room.status.field.choices,
        "room": room,
        "room_types": RoomType.objects.all()
    }

    if request.method == 'POST':
        data = request.POST
        attributes = {
            "name": data['name'],
            "status": data['state'],
            "description": data['description'],
            "room_type": RoomType.objects.get(id=data['room_type']),
            "price": data['price']
        }

        if Room.objects.filter(**attributes).exists():
            messages.error(request, 'Room already exists!', extra_tags="warning")
            return redirect('rooms:rooms_add')

        try:
            room = Room.objects.filter(id=room_id).update(**attributes)
            room = Room.objects.get(id=room_id)
            messages.success(request, f'Room: {room.name} updated successfully!', extra_tags="success")

            # Log activity
            action = f"Updated room: {room.name}"
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

            return redirect('rooms:rooms_list')
        except Exception as e:
            messages.error(request, 'There was an error during the update!', extra_tags="danger")
            return redirect('rooms:rooms_list')

    return render(request, "rooms_update.html", context=context)

@login_required(login_url="/authentication/login/")
def rooms_delete_view(request, room_id):
    try:
        room = Room.objects.get(id=room_id)
        room.delete()
        messages.success(request, f'Room: {room.name} deleted!', extra_tags="success")

        # Log activity
        action = f"Deleted room: {room.name}"
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

        return redirect('rooms:rooms_list')
    except Exception as e:
        messages.error(request, 'There was an error during the deletion!', extra_tags="danger")
        return redirect('rooms:rooms_list')


@login_required(login_url="/authentication/login/")
@csrf_exempt
def get_rooms_ajax_view(request):
    if request.method == 'POST' and is_ajax(request=request):
        data = []
        term = request.POST.get('term')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')

        # Filter rooms based on the search term and availability
        rooms = Room.objects.filter(name__icontains=term)

        # Additional filtering based on availability can be added here

        for room in rooms[0:10]:
            item = room.to_json()
            data.append(item)

        # Log activity
        action = f"Fetched rooms via AJAX"
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

        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)
