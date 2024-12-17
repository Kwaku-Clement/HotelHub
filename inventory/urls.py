from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('categories/', views.categories_list_view, name='category_list'),
    path('categories/add/', views.categories_add_view, name='category_create'),
    path('categories/update/<int:category_id>/', views.categories_update_view, name='category_update'),
    path('categories/delete/<int:category_id>/', views.categories_delete_view, name='category_delete'),

    path('products/', views.products_list_view, name='product_list'),
    path('products/add/', views.products_add_view, name='product_create'),
    path('products/update/<int:product_id>/', views.products_update_view, name='product_update'),
    path('products/delete/<int:product_id>/', views.products_delete_view, name='product_delete'),
    path('products/ajax/', views.get_products_ajax_view, name='get_products_ajax'),

    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('suppliers/update/<int:pk>/', views.supplier_update, name='supplier_update'),
    path('suppliers/delete/<int:pk>/', views.supplier_delete, name='supplier_delete'),

    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/add/', views.purchase_create, name='purchase_create'),
    path('purchases/update/<int:pk>/', views.purchase_update, name='purchase_update'),
    path('purchases/delete/<int:pk>/', views.purchase_delete, name='purchase_delete'),
    path('get-products/', views.get_supplier_products, name='get_supplier_products'),

    path('', views.home_view, name='home'),
]
