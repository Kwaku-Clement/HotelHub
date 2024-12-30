from datetime import timezone
from django import forms
from .models import Category, Miscellaneous, Product, Supplier, SupplierProduct, Purchase
from django.core.exceptions import ValidationError
from decimal import Decimal


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'status']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'description', 'category', 'price', 'quantity', 'status']

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['supplier_name', 'contact_info', 'status']

class SupplierProductForm(forms.ModelForm):
    class Meta:
        model = SupplierProduct
        fields = ['product_name', 'category_name', 'price', 'quantity']

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier', 'supplier_product', 'category_name', 'quantity', 'price_per_unit']

    def clean(self):
        cleaned_data = super().clean()
        supplier_product = cleaned_data.get("supplier_product")
        quantity = cleaned_data.get("quantity")
        price_per_unit = cleaned_data.get("price_per_unit")

        if not supplier_product:
            self.add_error('supplier_product', "Supplier product is required.")
            return cleaned_data

        if not quantity or quantity <= 0:
            self.add_error('quantity', "Quantity must be greater than zero.")
            return cleaned_data

        # Check if quantity exceeds available stock
        if quantity > supplier_product.quantity:
            self.add_error('quantity', f"Requested quantity ({quantity}) exceeds supplier's available quantity ({supplier_product.quantity}).")
            return cleaned_data

        if price_per_unit != supplier_product.price:
            self.add_error('price_per_unit', "Price does not match supplier's price")
            return cleaned_data

        if supplier_product and quantity and price_per_unit:
            cleaned_data["total_amount"] = Decimal(quantity) * Decimal(price_per_unit)
            # Set category_name from supplier_product if not provided
            if not cleaned_data.get('category_name'):
                cleaned_data['category_name'] = supplier_product.category_name

        return cleaned_data

    def save(self, commit=True):
        # Let the model's save method handle everything
        purchase = super().save(commit=False)
        
        if commit:
            try:
                purchase.save()
            except ValidationError as e:
                raise ValidationError(f"Error saving purchase: {str(e)}")
        
        return purchase
    


class MiscellaneousForm(forms.ModelForm):
    class Meta:
        model = Miscellaneous
        fields = ['type', 'amount', 'date', 'description']
