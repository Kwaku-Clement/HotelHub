from django.urls import path
from . import views

app_name = "rooms"
urlpatterns = [
    path('room_types', views.room_types_list_view, name='room_types_list'),
    path('room_types/add', views.room_types_add_view, name='room_types_add'),
    path('room_types/update/<int:room_type_id>', views.room_types_update_view, name='room_types_update'),
    path('room_types/delete/<int:room_type_id>', views.room_types_delete_view, name='room_types_delete'),
    
    path('', views.rooms_list_view, name='rooms_list'),
    path('add', views.rooms_add_view, name='rooms_add'),
    path('update/<int:room_id>', views.rooms_update_view, name='rooms_update'),
    path('delete/<int:room_id>', views.rooms_delete_view, name='rooms_delete'),
    path("get", views.get_rooms_ajax_view, name="get_rooms"),
]
