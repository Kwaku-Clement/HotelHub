from django import forms
from .models import Supplier, Purchase, Product, Category
import unicodedata
import re
from django.core.exceptions import ValidationError

class BaseFormMixin:
    """Base mixin for common form functionality"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            # Add Bootstrap classes
            css_classes = field.widget.attrs.get("class", "")
            if "form-control" not in css_classes:
                css_classes = f"{css_classes} form-control".strip()

            field.widget.attrs.update({
                "class": css_classes,
                "placeholder": field.label or "",
            })

            # Add required attribute if field is required
            if field.required:
                field.widget.attrs["required"] = "required"

class SupplierForm(BaseFormMixin, forms.ModelForm):
    """Form for creating and updating suppliers"""

    class Meta:
        model = Supplier
        fields = ["supplier_name", "contact_info", "product", "category", "price", "quantity", "status"]
        widgets = {
            "supplier_name": forms.TextInput(
                attrs={"placeholder": "Enter supplier name"}
            ),
            "contact_info": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Enter contact information"
                }
            ),
            "product": forms.TextInput(
                attrs={"placeholder": "Enter product name"}
            ),
            "category": forms.TextInput(
                attrs={"placeholder": "Enter category name"}
            ),
            "price": forms.NumberInput(
                attrs={"step": "0.01", "min": "0"}
            ),
            "quantity": forms.NumberInput(
                attrs={"step": "1", "min": "0"}
            ),
            "status": forms.Select()
        }

    def clean_supplier_name(self):
        name = self.cleaned_data.get("supplier_name")
        if name:
            normalized_name = "".join(
                c for c in unicodedata.normalize("NFD", name)
                if unicodedata.category(c) != "Mn"
            )
            normalized_name = re.sub(r"\s+", "", normalized_name.lower())

            existing_suppliers = Supplier.objects.exclude(
                id=self.instance.id if self.instance else None
            )
            for supplier in existing_suppliers:
                supplier_normalized = "".join(
                    c for c in unicodedata.normalize("NFD", supplier.supplier_name)
                    if unicodedata.category(c) != "Mn"
                )
                supplier_normalized = re.sub(r"\s+", "", supplier_normalized.lower())
                if supplier_normalized == normalized_name:
                    raise ValidationError(
                        f"A supplier with a similar name already exists: '{supplier.supplier_name}'"
                    )
        return name

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity is not None and quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

class PurchaseForm(BaseFormMixin, forms.ModelForm):
    """Form for creating and updating purchases"""

    class Meta:
        model = Purchase
        fields = ["supplier", "supplier_product", "supplier_category", "quantity"]
        widgets = {
            "supplier": forms.Select(
                attrs={"required": True}
            ),
            "supplier_product": forms.TextInput(
                attrs={"readonly": True}
            ),
            "supplier_category": forms.TextInput(
                attrs={"readonly": True}
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "min": "1",
                    "step": "1",
                    "required": True
                }
            )
        }
        labels = {
            "supplier": "Select Supplier",
            "supplier_product": "Product",
            "supplier_category": "Category",
            "quantity": "Quantity"
        }
        help_texts = {
            "quantity": "Enter the number of units to purchase"
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if "supplier" in self.data:
            try:
                supplier_id = int(self.data.get("supplier"))
                supplier = Supplier.objects.get(id=supplier_id)
                self.fields["supplier_product"].initial = supplier.product
                self.fields["supplier_category"].initial = supplier.category
            except (ValueError, TypeError, Supplier.DoesNotExist):
                pass
        elif self.instance.pk:
            self.fields["supplier"].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        supplier = cleaned_data.get("supplier")
        quantity = cleaned_data.get("quantity")

        if supplier and quantity:
            # Validate supplier has enough quantity
            if quantity > supplier.quantity:
                raise ValidationError({
                    "quantity": f"Requested quantity ({quantity}) exceeds available quantity ({supplier.quantity})."
                })

            # Set supplier-specific fields
            cleaned_data["supplier_product"] = supplier.product
            cleaned_data["supplier_category"] = supplier.category
            cleaned_data["price_per_unit"] = supplier.price
            cleaned_data["total_amount"] = quantity * supplier.price

        return cleaned_data

# Keep CategoryForm and ProductForm unchanged since they weren't affected by the model changes
class CategoryForm(BaseFormMixin, forms.ModelForm):
    """Form for creating and updating categories"""

    class Meta:
        model = Category
        fields = ["name", "description", "status"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter category name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter category description",
                    "rows": 3,
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            normalized_name = "".join(
                c
                for c in unicodedata.normalize("NFD", name)
                if unicodedata.category(c) != "Mn"
            )
            normalized_name = re.sub(r"\s+", "", normalized_name.lower())

            # Check for existing categories with similar names
            existing_categories = Category.objects.exclude(
                id=self.instance.id if self.instance else None
            )
            for category in existing_categories:
                category_normalized = "".join(
                    c
                    for c in unicodedata.normalize("NFD", category.name)
                    if unicodedata.category(c) != "Mn"
                )
                category_normalized = re.sub(r"\s+", "", category_normalized.lower())
                if category_normalized == normalized_name:
                    raise ValidationError(
                        f"A category with a similar name already exists: '{category.name}'"
                    )
        return name


class ProductForm(BaseFormMixin, forms.ModelForm):
    """Form for creating and updating products"""

    class Meta:
        model = Product
        fields = [
            "category",
            "product_name",
            "description",
            "price",
            "status",
            "quantity",
        ]
        widgets = {
            "category": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "product_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter product name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter product description",
                    "rows": 3,
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Enter price",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "placeholder": "Enter quantity",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(
            status="ACTIVE"
        ).order_by("name")

    def clean_product_name(self):
        product_name = self.cleaned_data.get("product_name")
        if product_name:
            normalized_name = "".join(
                c
                for c in unicodedata.normalize("NFD", product_name)
                if unicodedata.category(c) != "Mn"
            )
            normalized_name = re.sub(r"\s+", "", normalized_name.lower())

            # Check for existing products with similar names
            existing_products = Product.objects.exclude(
                id=self.instance.id if self.instance else None
            )
            if existing_products.filter(product_name__iexact=normalized_name).exists():
                raise ValidationError("A product with a similar name already exists.")
        return product_name
