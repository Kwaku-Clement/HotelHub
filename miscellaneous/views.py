from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Miscellaneous
from .forms import MiscellaneousForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

@login_required(login_url="/authentication/login/")
def miscellaneous_list_view(request):
    context = {
        "active_icon": "miscellaneous",
        "miscellaneous": Miscellaneous.objects.all()
    }
    return render(request, "miscellaneous_list.html", context=context)

@login_required(login_url="/authentication/login/")
def miscellaneous_add_view(request):
    context = {
        "active_icon": "miscellaneous",
    }

    if request.method == 'POST':
        form = MiscellaneousForm(request.POST)
        if form.is_valid():
            miscellaneous = form.save(commit=False)
            miscellaneous.created_by = request.user
            miscellaneous.save()
            messages.success(request, 'Miscellaneous expense created successfully!', extra_tags="success")
            return redirect('miscellaneous:miscellaneous_list')
        else:
            messages.error(request, 'There was an error creating the miscellaneous expense.', extra_tags="danger")
    else:
        form = MiscellaneousForm()

    context["form"] = form
    return render(request, "miscellaneous_add.html", context=context)

@login_required(login_url="/authentication/login/")
def miscellaneous_update_view(request, miscellaneous_id):
    miscellaneous = get_object_or_404(Miscellaneous, id=miscellaneous_id)
    context = {
        "active_icon": "miscellaneous",
        "miscellaneous": miscellaneous
    }

    if request.method == 'POST':
        form = MiscellaneousForm(request.POST, instance=miscellaneous)
        if form.is_valid():
            form.save()
            messages.success(request, 'Miscellaneous expense updated successfully!', extra_tags="success")
            return redirect('miscellaneous:miscellaneous_list')
        else:
            messages.error(request, 'There was an error updating the miscellaneous expense.', extra_tags="danger")
    else:
        form = MiscellaneousForm(instance=miscellaneous)

    context["form"] = form
    return render(request, "miscellaneous_update.html", context=context)


@csrf_exempt
@login_required(login_url="/authentication/login/")
def miscellaneous_delete_view(request, miscellaneous_id):
    if request.method == 'POST':
        miscellaneous = get_object_or_404(Miscellaneous, id=miscellaneous_id)
        miscellaneous.delete()
        return JsonResponse({'status': 'success', 'msg': 'Miscellaneous expense deleted successfully!'})
    return JsonResponse({'status': 'error', 'msg': 'Invalid request method.'})
