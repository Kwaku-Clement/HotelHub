from django import forms
from .models import Supplier, Purchase, Product, Category, SupplierProduct
import unicodedata
import re
from django.core.exceptions import ValidationError

class BaseFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control",
                "placeholder": field.label
            })

class SupplierForm(BaseFormMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['supplier_name', 'contact_info']
        labels = {
            'supplier_name': 'Supplier Name',
            'contact_info': 'Contact Information',
        }
        widgets = {
            'contact_info': forms.Textarea(attrs={'rows': 3}),
        }

class SupplierProductForm(BaseFormMixin, forms.ModelForm):
    class Meta:
        model = SupplierProduct
        fields = ['product_name', 'description', 'price', 'quantity']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'step': '1'}),
        }


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier', 'product', 'quantity', 'price']
        widgets = {
            'supplier': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'product': forms.Select(attrs={
                'class': 'form-control',
                'required': True,
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '1',
                'required': True,
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01',
                'required': True,
            })
        }
        labels = {
            'supplier': 'Select Supplier',
            'product': 'Select Product',
            'quantity': 'Quantity',
            'price': 'Price per Unit'
        }
        help_texts = {
            'quantity': 'Enter the number of units to purchase',
            'price': 'Enter the price per unit'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize product choices as empty
        self.fields['product'].queryset = SupplierProduct.objects.none()
        
        if 'supplier' in self.data:
            try:
                supplier_id = int(self.data.get('supplier'))
                self.fields['product'].queryset = SupplierProduct.objects.filter(
                    supplier_id=supplier_id
                ).order_by('product_name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            # If this is an edit form, populate product choices for the selected supplier
            self.fields['supplier'].disabled = True
            self.fields['product'].queryset = SupplierProduct.objects.filter(
                supplier=self.instance.supplier
            ).order_by('product_name')
            self.initial['price'] = self.instance.price

    def clean(self):
        cleaned_data = super().clean()
        supplier = cleaned_data.get('supplier')
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        price = cleaned_data.get('price')

        if supplier and product:
            if product.supplier != supplier:
                raise ValidationError({
                    'product': 'Selected product does not belong to the selected supplier.'
                })

        if quantity is not None and quantity <= 0:
            raise ValidationError({
                'quantity': 'Quantity must be greater than zero.'
            })

        if price is not None and price <= 0:
            raise ValidationError({
                'price': 'Price must be greater than zero.'
            })

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.total = instance.quantity * instance.price
        
        if commit:
            instance.save()
        return instance


class CategoryForm(BaseFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        labels = {
            'name': 'Name',
            'description': 'Description',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Sweet Wine',
            }),
            'description': forms.Textarea(attrs={
                'placeholder': 'Enter general information, etc.',
                'rows': 3,
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            normalized_name = ''.join(c for c in unicodedata.normalize('NFD', name)
                                      if unicodedata.category(c) != 'Mn')
            normalized_name = re.sub(r'\s+', '', normalized_name.lower())
            instance = self.instance
            existing_categories = Category.objects.exclude(id=instance.id)
            for category in existing_categories:
                category_normalized = ''.join(c for c in unicodedata.normalize('NFD', category.name)
                                              if unicodedata.category(c) != 'Mn')
                category_normalized = re.sub(r'\s+', '', category_normalized.lower())
                if category_normalized == normalized_name:
                    raise ValidationError(f"A similar category already exists: '{category.name}'")
        return name


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'product_name', 'description', 'price', 'status', 'quantity']
        labels = {
            'category': 'Category',
            'product_name': 'Product Name',
            'description': 'Description',
            'price': 'Price',
            'status': 'Status',
            'quantity': 'Quantity',
        }
        widgets = {
            'price': forms.NumberInput(attrs={
                'placeholder': 'Enter the product price',
                'step': '0.01',
            }),
            'status': forms.Select(choices=[
                ("ACTIVE", 'Active'),
                ("INACTIVE", 'Inactive')
            ]),
            'quantity': forms.NumberInput(attrs={
                'placeholder': 'Enter the product quantity',
                'min': '0',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all().order_by('name')
        self.fields['status'].disabled = False  # Ensure the status field is not disabled

    @staticmethod
    def normalize_text(text):
        if text:
            text = ''.join(c for c in unicodedata.normalize('NFD', text)
                           if unicodedata.category(c) != 'Mn')
            text = re.sub(r'[^\w]', '', text.lower())
        return text

    def clean(self):
        cleaned_data = super().clean()
        product_name = cleaned_data.get('product_name')

        if product_name:
            normalized_name = self.normalize_text(product_name)
            instance_id = self.instance.pk if self.instance.pk else None
            name_duplicates = Product.objects.all()
            if instance_id:
                name_duplicates = name_duplicates.exclude(pk=instance_id)

            for product in name_duplicates:
                if self.normalize_text(product.product_name) == normalized_name:
                    self.add_error('product_name', "A product with a similar name already exists.")
                    raise forms.ValidationError("A product with a similar name already exists.")

        return cleaned_data


