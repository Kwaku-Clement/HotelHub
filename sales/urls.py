# urls.py
from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sales_list_view, name='sales_list'),
    path('manage/', views.create_update_sales_view, name='manage_sales'),
    path('manage/<int:sale_id>/', views.create_update_sales_view, name='manage_sales'),
    path('delete/<int:sale_id>/', views.delete_sales_view, name='delete_sales'),
    path('receipt/<int:sale_id>/', views.receipt_view, name='receipt'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('revert/<int:sale_id>/', views.revert_sales_view, name='revert_sales'),
]