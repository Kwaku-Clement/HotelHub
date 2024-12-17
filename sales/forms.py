from django import forms
from .models import Sales, SalesItems

class SalesForm(forms.ModelForm):
    class Meta:
        model = Sales
        fields = ['code', 'sub_total', 'grand_total', 'tax_amount', 'tax', 'amount_payed', 'amount_change', 'client']
        labels = {
            'code': 'Code',
            'sub_total': 'Sub Total',
            'grand_total': 'Grand Total',
            'tax_amount': 'Tax Amount',
            'tax': 'Tax',
            'amount_payed': 'Amount Payed',
            'amount_change': 'Amount Change',
            'client': 'Client',
        }

class SalesItemsForm(forms.ModelForm):
    class Meta:
        model = SalesItems
        fields = ['sale', 'product', 'price', 'qty', 'total']
        labels = {
            'sale': 'Sale',
            'product': 'Product',
            'price': 'Price',
            'qty': 'Quantity',
            'total': 'Total',
        }
