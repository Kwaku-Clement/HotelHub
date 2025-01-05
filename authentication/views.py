from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import LoginForm, ChangePasswordForm, UserRegistrationForm
from .models import Users

def superuser_check(user):
    return user.is_superuser

@ensure_csrf_cookie
def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None

    if request.method == "POST" and form.is_valid():
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            if not hasattr(user, 'role') or not user.role:
                user.role = 'admin'
                user.save()

            request.session['user_role'] = user.role
            request.session.cycle_key()
            return redirect("/")
        msg = 'Invalid username or password!'

    return render(request, "login.html", {"form": form, "msg": msg})

@login_required(login_url="/authentication/login/")
def register_user(request):
    context = {
        "active_icon": 'users',
    }

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = form.cleaned_data.get('role')
            user.save()
            messages.success(request, f'User {form.cleaned_data["first_name"]} {form.cleaned_data["last_name"]} created successfully', extra_tags="success")
            return redirect('authentication:users_list')
        else:
            messages.error(request, 'There was an error creating the user', extra_tags='danger')
    else:
        form = UserRegistrationForm()

    context['form'] = form
    return render(request, "register.html", context=context)

@login_required(login_url="/authentication/login/")
def update_users_view(request, user_id):
    try:
        user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        messages.error(request, 'User not found!', extra_tags='danger')
        return redirect('authentication:users_list')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User: {user.get_full_name()} updated successfully!', extra_tags="success")
            return redirect('authentication:users_list')
        else:
            messages.error(request, 'There was an error during the update!', extra_tags="danger")
    else:
        form = UserRegistrationForm(instance=user)

    context = {
        "active_icon": 'users',
        "form": form,
        "user": user
    }
    return render(request, 'update_user.html', context=context)

@login_required(login_url="/authentication/login/")
def delete_user(request, user_id):
    try:
        user = Users.objects.get(id=user_id)
        user.delete()
        messages.success(request, f'User: {user.get_full_name()} deleted!', extra_tags="success")
        return redirect('authentication:users_list')
    except Exception as e:
        messages.error(request, 'There was an error during the deletion!', extra_tags="danger")
        return redirect('authentication:users_list')

@login_required
def users_list_view(request):
    context = {
        "active_icon": 'users',
        "users": Users.objects.all()
    }
    return render(request, "users_list.html", context=context)

@login_required
def user_profile(request):
    user = request.user

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!', extra_tags="success")
        else:
            messages.error(request, 'There was an error during the update!', extra_tags="danger")
        return redirect('authentication:user_profile')
    else:
        form = UserRegistrationForm(instance=user)

    context = {
        "active_icon": 'profile',
        "form": form,
        "user": user,
    }
    return render(request, 'user_profile.html', context=context)

@login_required
def change_password(request):
    context = {
        "active_icon": 'users'
    }
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('authentication:login')
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'change_password.html', {'form': form})
