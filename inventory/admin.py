from django.contrib import admin
from .models import Category, Supplier, Product, SupplierProduct, Purchase

admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(SupplierProduct)
admin.site.register(Purchase)
