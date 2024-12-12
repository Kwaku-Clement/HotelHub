from django.urls import path
from .views import delete_user, login_view, register_user, change_password, update_users_view, user_profile, users_list_view
from django.contrib.auth.views import LogoutView


app_name = "authentication"
urlpatterns = [
    path('login/', login_view, name="login"),
    path('register/', register_user, name="register"),
    path('users_list/', users_list_view, name="users_list"),
    path('change_password/', change_password, name="change_password"),
    path("logout/", LogoutView.as_view(next_page='authentication:login'), name="logout"),
    path('delete/<int:user_id>', delete_user, name='delete_user'),
    path('update/<int:user_id>', update_users_view, name='update_user'),
    path('user_profile/', user_profile, name='user_profile'),

]
