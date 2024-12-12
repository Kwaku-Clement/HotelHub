from django.urls import path
from . import views

app_name = "guests"
urlpatterns = [
    path('', views.guests_list_view, name='guests_list'),
    path('add', views.guests_add_view, name='guests_add'),
    path('update/<int:guest_id>', views.guests_update_view, name='guests_update'),
    path('delete/<int:guest_id>', views.guests_delete_view, name='guests_delete'),
]
