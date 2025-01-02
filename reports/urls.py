from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Main report selection page
    path('generate_report/', views.generate_report, name='select_report'),

    # Store report URLs
    path('store/', views.generate_store_report, name='store_report'),
    path('store/<str:start_date>/<str:end_date>/', views.generate_store_report, name='store_report_with_date'),

    # Reservation report URLs
    path('reservation/', views.generate_reservation_report, name='reservation_report'),
    path('reservation/<str:start_date>/<str:end_date>/', views.generate_reservation_report, name='reservation_report_with_date'),
]
