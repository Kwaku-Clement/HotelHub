from django.db import models
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal

class Category(models.Model):
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )

    name = models.CharField(max_length=256, unique=True)
    description = models.TextField(max_length=256)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        default="ACTIVE",
    )
    purchase_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "categories"
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
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.PROTECT
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=100,
        default="ACTIVE",
    )
    purchase_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        unique_together = ['product_name', 'category']

    def __str__(self):
        return f"{self.product_name} ({self.category.name})"

    def to_select2(self):
        return {
            'id': self.id,
            'text': self.product_name,
            'price': str(self.price),  # Convert Decimal to string for JSON serialization
        }

class Supplier(models.Model):
    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive")
    )

    supplier_name = models.CharField(max_length=100)
    contact_info = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )
    purchase_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "suppliers"
        ordering = ['supplier_name']
        unique_together = ['supplier_name', 'contact_info']  # Add composite unique constraint

    def __str__(self):
        return self.supplier_name
    
class SupplierProduct(models.Model):
    supplier = models.ForeignKey(Supplier, related_name='supplier_products', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=256)
    category_name = models.CharField(max_length=256)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    purchase_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "supplier_products"
        unique_together = ['supplier', 'product_name', 'category_name']

    def __str__(self):
        return f"{self.supplier.supplier_name} - {self.product_name}"

    def update_quantity(self, quantity_change):
        """Update available quantity"""
        with transaction.atomic():
            new_quantity = self.quantity + quantity_change
            if new_quantity < 0:
                raise ValidationError(f"Insufficient Stock. Available: {self.quantity}, Requested change: {abs(quantity_change)}")
            self.quantity = new_quantity
            self.save()

class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchases')
    supplier_product = models.ForeignKey(SupplierProduct, on_delete=models.PROTECT, related_name='purchases')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='purchases', null=True)
    category_name = models.CharField(max_length=255, default='Default Category')
    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    purchase_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "purchases"

    def clean(self):
        if not self.supplier_product:
            raise ValidationError("Supplier product is required.")
        if self.quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        if self.quantity > self.supplier_product.quantity:
            raise ValidationError(f"Requested quantity ({self.quantity}) exceeds supplier's available quantity ({self.supplier_product.quantity}).")
        if self.price_per_unit != self.supplier_product.price:
            raise ValidationError("Price does not match supplier's price.")

    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity) * Decimal(self.price_per_unit)

        with transaction.atomic():
            # Validate the purchase
            self.clean()

            # Get or create category
            category, created = Category.objects.get_or_create(
                name=self.category_name,
                defaults={
                    'description': f"Category for {self.category_name}",
                    'status': 'ACTIVE'
                }
            )

            # Get or create product
            product, created = Product.objects.get_or_create(
                product_name=self.supplier_product.product_name,
                category=category,
                defaults={
                    'description': f"Product from {self.supplier.supplier_name}",
                    'price': self.supplier_product.price,
                    'quantity': 0,
                    'status': 'ACTIVE'
                }
            )

            if not created and product.price != self.supplier_product.price:
                product.price = self.supplier_product.price
                product.save()

            self.product = product

            # Calculate quantity changes
            if self.pk:
                previous = Purchase.objects.get(pk=self.pk)
                quantity_difference = self.quantity - previous.quantity
            else:
                quantity_difference = self.quantity

            try:
                # First update the supplier product quantity
                self.supplier_product.update_quantity(-quantity_difference)
                
                # Then update the product quantity
                product.quantity = max(0, product.quantity + quantity_difference)
                product.save()
                
                # Finally save the purchase
                super().save(*args, **kwargs)
                
            except ValidationError as e:
                # Rollback is automatic due to transaction.atomic()
                raise ValidationError(f"Error processing purchase: {str(e)}")


class Miscellaneous(models.Model):
    TYPE_CHOICES = (
        ("UTILITY", "Utility"),
        ("RENT", "Rent"),
        ("SALARIES", "Salaries"),
        ("OTHER", "Other")
    )

    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "store_miscellaneous"

    def __str__(self):
        return f"{self.type} - {self.amount}"
