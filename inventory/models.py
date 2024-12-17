from django.db import models
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

class Category(models.Model):
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )

    name = models.CharField(max_length=256)
    description = models.TextField(max_length=256)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        verbose_name="Status of the category",
    )

    class Meta:
        db_table = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Product(models.Model):
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )

    product_name = models.CharField(max_length=256)
    description = models.TextField(max_length=256)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        verbose_name="Status of the product",
    )
    category = models.ForeignKey(
        'Category', related_name="category", on_delete=models.CASCADE, db_column='category')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.IntegerField(default=0, null=False, blank=False)

    class Meta:
        db_table = "Product"

    def __str__(self):
        return self.product_name

    def update_quantity_on_sale(self, quantity_sold):
        self.quantity -= quantity_sold
        self.save()

    def increase_quantity(self, quantity_added):
        self.quantity += quantity_added
        self.save()

    def to_select2(self):
        return {
            'id': self.id,
            'text': self.product_name,
            'price': float(self.price)
        }


class Supplier(models.Model):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]
    
    supplier_name = models.CharField(max_length=100)
    contact_info = models.TextField(blank=True)
    date_added = models.DateTimeField(default=timezone.now, editable=False)
    date_updated = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=ACTIVE,
    )

    def __str__(self):
        return self.supplier_name

    class Meta:
        ordering = ['supplier_name']

class SupplierProduct(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    product_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(default=0.00, max_digits=18, decimal_places=2)
    quantity = models.DecimalField(max_digits=10, decimal_places=0, default=0.00)
    date_added = models.DateTimeField(default=timezone.now, editable=False)
    date_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['supplier', 'product_name']
        ordering = ['supplier', 'product_name']

    def __str__(self):
        return f"{self.product_name} ({self.supplier.supplier_name})"

class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='supplier_purchases', default=1)
    product = models.ForeignKey(SupplierProduct, on_delete=models.PROTECT, related_name='purchases', default=1)
    quantity = models.DecimalField(max_digits=10, decimal_places=0, default=0.00)
    price = models.DecimalField(default=0.00,max_digits=18, decimal_places=2)
    total = models.DecimalField(max_digits=18, decimal_places=2, editable=False, default=0.00)
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['supplier']),
            models.Index(fields=['product']),
        ]

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("The quantity must be greater than zero.")
        if self.price <= 0:
            raise ValidationError("The price must be greater than zero.")
        if self.product and self.product.supplier != self.supplier:
            raise ValidationError("The selected product does not belong to the selected supplier.")

    def save(self, *args, **kwargs):
        self.clean()
        self.total = self.price * self.quantity

        with transaction.atomic():
            if self.pk:
                previous_instance = Purchase.objects.select_related('product').get(pk=self.pk)
                quantity_difference = self.quantity - previous_instance.quantity
            else:
                quantity_difference = self.quantity

            super().save(*args, **kwargs)

            if self.product:
                self.product.quantity += quantity_difference
                self.product.price = self.price  # Update the product price with the latest purchase price
                self.product.save()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            if self.product:
                self.product.quantity -= self.quantity
                self.product.save()
            super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.product} - {self.quantity} @ ${self.price} each"
    