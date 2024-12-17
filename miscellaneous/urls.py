from django.urls import path
from . import views

app_name = 'miscellaneous'

urlpatterns = [
    path('list/', views.miscellaneous_list_view, name='miscellaneous_list'),
    path('add/', views.miscellaneous_add_view, name='miscellaneous_add'),
    path('update/<int:miscellaneous_id>/', views.miscellaneous_update_view, name='miscellaneous_update'),
    path('delete/<int:miscellaneous_id>/', views.miscellaneous_delete_view, name='miscellaneous_delete'),
]
