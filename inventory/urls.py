from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('categories/', views.categories_list_view, name='category_list'),
    path('categories/add/', views.category_create_update, name='category_create_update'),
    path('categories/update/<int:category_id>/', views.category_create_update, name='category_create_update'),
    path('categories/delete/<int:category_id>/', views.categories_delete_view, name='category_delete'),

    path('products/', views.products_list_view, name='product_list'),
    path('products/add/', views.product_create_update, name='product_create_update'),
    path('products/update/<int:product_id>/', views.product_create_update, name='product_create_update'),
    path('products/delete/<int:product_id>/', views.products_delete_view, name='product_delete'),

    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create_update, name='supplier_create_update'),
    path('suppliers/update/<int:pk>/', views.supplier_create_update, name='supplier_create_update'),
    path('suppliers/delete/<int:pk>/', views.supplier_delete, name='supplier_delete'),

    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/add/', views.purchase_create_update, name='purchase_create_update'),
    path('purchases/update/<int:pk>/', views.purchase_create_update, name='purchase_create_update'),
    path('purchases/delete/<int:pk>/', views.purchase_delete, name='purchase_delete'),
    
    path('supplier/<int:supplier_id>/products/', views.get_supplier_products, name='get_supplier_products'),
    path('supplier-product/<int:product_id>/', views.get_supplier_product_details, name='get_supplier_product_details'),
    
    path('add-miscellaneous/', views.add_miscellaneous, name='add_miscellaneous'),

    path('', views.home_view, name='home'),
]
