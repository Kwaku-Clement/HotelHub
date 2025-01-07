from django.urls import path
from . import views

app_name = "reservations"

urlpatterns = [
    path('reservations/', views.reservations_list_view, name='reservations_list'),
    path('reservations/add/', views.reservations_add_create_view, name='reservations_add'),
    path('reservations/<int:reservation_id>/', views.reservations_details_view, name='reservations_details'),
    path('reservations/<int:reservation_id>/pdf/', views.receipt_pdf_view, name='reservations_receipt_pdf'),
    path('reservations/<int:reservation_id>/delete/', views.reservations_delete, name='reservations_delete'),
    path('reservations/<int:reservation_id>/edit/', views.reservations_add_create_view, name='reservations_edit'),
]