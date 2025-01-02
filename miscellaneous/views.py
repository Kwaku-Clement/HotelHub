from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from miscellaneous.models import Miscellaneous
from .forms import MiscellaneousForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

@login_required(login_url="/authentication/login/")
def miscellaneous_list_view(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_term = request.GET.get('search')

    queryset = Miscellaneous.objects.all()

    if start_date and end_date:
        queryset = queryset.filter(date__range=[start_date, end_date])

    if search_term:
        queryset = queryset.filter(
            Q(type__icontains=search_term) |
            Q(description__icontains=search_term) |
            Q(amount__icontains=search_term)
        )

    context = {
        "active_icon": "miscellaneous",
        "miscellaneous": queryset,
        "start_date": start_date,
        "end_date": end_date,
        "search_term": search_term,
    }
    return render(request, "miscellaneous_list.html", context=context)

@login_required(login_url="/authentication/login/")
def miscellaneous_add_create_view(request, miscellaneous_id=None):
    context = {
        "active_icon": "miscellaneous",
    }

    if miscellaneous_id:
        miscellaneous = get_object_or_404(Miscellaneous, id=miscellaneous_id)
        context["miscellaneous"] = miscellaneous
        form = MiscellaneousForm(request.POST or None, instance=miscellaneous)
        success_message = 'Miscellaneous expense updated successfully!'
    else:
        form = MiscellaneousForm(request.POST or None)
        success_message = 'Miscellaneous expense created successfully!'

    if request.method == 'POST' and form.is_valid():
        miscellaneous = form.save(commit=False)
        if not miscellaneous_id:
            miscellaneous.created_by = request.user
            miscellaneous.date = timezone.now()  # Automatically set the date to the current date and time
        miscellaneous.save()
        messages.success(request, success_message, extra_tags="success")
        return redirect('miscellaneous:miscellaneous_list')

    elif request.method == 'POST':
        messages.error(request, 'There was an error with the miscellaneous expense.', extra_tags="danger")

    context["form"] = form
    return render(request, "miscellaneous_add.html", context=context)

@csrf_exempt
@login_required(login_url="/authentication/login/")
def miscellaneous_delete_view(request, miscellaneous_id):
    if request.method == 'POST':
        miscellaneous = get_object_or_404(Miscellaneous, id=miscellaneous_id)
        miscellaneous.delete()
        return JsonResponse({'status': 'success', 'msg': 'Miscellaneous expense deleted successfully!'})
    return JsonResponse({'status': 'error', 'msg': 'Invalid request method.'})
