from django import forms
from .models import Miscellaneous

class MiscellaneousForm(forms.ModelForm):
    class Meta:
        model = Miscellaneous
        fields = ['type', 'description', 'amount', 'date', 'created_by']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'created_by': forms.Select(attrs={'class': 'form-control'}),
        }
