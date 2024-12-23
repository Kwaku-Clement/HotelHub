from django.contrib import admin
from .models import Category, Supplier, Product, Purchase

# Register the models
admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(Purchase)
