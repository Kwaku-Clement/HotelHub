from django.urls import path
from . import views

app_name = "reservations"

urlpatterns = [
    path("", views.reservations_list_view, name="reservations_list"),
    path("list/", views.reservations_list_view, name="reservations_list"),
    path("add/", views.reservations_add_view, name="reservations_add"),
    path("edit/<int:reservation_id>/", views.reservations_add_view, name="reservations_edit"),
    path("delete/<int:id>/", views.reservations_delete, name="reservations_delete"),
    path("details/<int:reservation_id>/", views.reservations_details_view, name="reservations_details"),
    path("pdf/<int:reservation_id>/", views.receipt_pdf_view, name="reservations_receipt_pdf"),
    path("update_status/<int:reservation_id>/<str:status>/", views.update_reservation_status_view, name="update_reservation_status"),
]
