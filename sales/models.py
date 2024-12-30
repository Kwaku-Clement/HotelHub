from datetime import datetime
from django.db import models, transaction
from django.utils import timezone
from authentication.models import Users
from inventory.models import Product
from decimal import Decimal

class Sales(models.Model):
    code = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_payed = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_change = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(default=timezone.now)
    client = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            sales_today = Sales.objects.filter(date_added__date=timezone.now().date()).count()
            self.code = f"SALE-{sales_today + 1:04d}"
            while Sales.objects.filter(code=self.code).exists():
                sales_today += 1
                self.code = f"SALE-{sales_today:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

class SalesItems(models.Model):
    sale = models.ForeignKey(Sales, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    qty = models.IntegerField(default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        self.price = self.product.price
        self.total = self.price * self.qty
        super().save(*args, **kwargs)
        self.update_product_quantity()

    def update_product_quantity(self):
        self.product.quantity -= self.qty
        self.product.save()

    def delete(self, *args, **kwargs):
        self.product.quantity += self.qty
        self.product.save()
        super().delete(*args, **kwargs)
