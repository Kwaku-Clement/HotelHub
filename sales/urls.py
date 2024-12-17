from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('sales/', views.sales_list_view, name='sales_list'),
    path('sales/create/', views.create_sales_view, name='create_sales'),
    path('sales/receipt/<int:sale_id>/', views.receipt_view, name='receipt'),
    path('sales/delete/<int:sale_id>/', views.delete_sales_view, name='delete_sales'),
    path('sales/update/<int:sale_id>/', views.update_sales_view, name='update_sales'),
    path('sales/details/<int:sale_id>/', views.sales_details_view, name='sales_details'),
    path('sales/checkout-modal/', views.checkout_modal, name='checkout_modal'),
    path('sales/process-payment/', views.process_payment, name='process_payment'),
]