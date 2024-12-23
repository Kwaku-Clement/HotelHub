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
        Category, related_name="products", on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.IntegerField(default=0)

    class Meta:
        db_table = "Product"

    def __str__(self):
        return self.product_name

class Supplier(models.Model):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]

    supplier_name = models.CharField(max_length=100)
    contact_info = models.TextField(blank=True)
    product = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    date_added = models.DateTimeField(default=timezone.now, editable=False)
    date_updated = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=ACTIVE,
    )

    class Meta:
        ordering = ['supplier_name']

    def __str__(self):
        return self.supplier_name

class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchases')
    # Links to supplier's product and category
    supplier_product = models.CharField(max_length=100)
    supplier_category = models.CharField(max_length=100)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, editable=False)
    
    # Links to main Product and Category models
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='purchases')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='purchases')
    
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['supplier']),
            models.Index(fields=['product']),
            models.Index(fields=['category']),
        ]

    def clean(self):
        if not self.supplier:
            raise ValidationError("Supplier is required.")
        if self.quantity <= 0:
            raise ValidationError("The quantity must be greater than zero.")
        if self.price_per_unit <= 0:
            raise ValidationError("The price must be greater than zero.")
        
        # Validate that selected product and category match supplier's offerings
        if self.supplier_product != self.supplier.product:
            raise ValidationError("Selected product does not match supplier's product.")
        if self.supplier_category != self.supplier.category:
            raise ValidationError("Selected category does not match supplier's category.")
        if self.price_per_unit != self.supplier.price:
            raise ValidationError("Price does not match supplier's price.")
        if self.quantity > self.supplier.quantity:
            raise ValidationError("Requested quantity exceeds supplier's available quantity.")

    def save(self, *args, **kwargs):
        # Calculate total amount
        self.total_amount = self.quantity * self.price_per_unit
        
        with transaction.atomic():
            # Run validation
            self.clean()
            
            if self.pk:
                # If updating existing purchase
                previous = Purchase.objects.get(pk=self.pk)
                quantity_difference = self.quantity - previous.quantity
            else:
                # If new purchase
                quantity_difference = self.quantity

            # Update supplier's quantity
            self.supplier.quantity -= quantity_difference
            self.supplier.save()

            # Update product's quantity
            self.product.quantity += quantity_difference
            self.product.save()

            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            # Restore quantities
            self.supplier.quantity += self.quantity
            self.supplier.save()
            
            self.product.quantity -= self.quantity
            self.product.save()
            
            super().delete(*args, **kwargs)

    def __str__(self):
        return f"Purchase from {self.supplier.supplier_name} - {self.supplier_product} ({self.quantity} units)"