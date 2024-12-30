from django import forms
from datetime import date, timedelta

class ReportSelectionForm(forms.Form):
    REPORT_TYPE_CHOICES = [
        ('financial', 'Financial Report'),
    ]

    report_type = forms.ChoiceField(choices=REPORT_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    start_date = forms.DateField(initial=date.today() - timedelta(days=30), widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    end_date = forms.DateField(initial=date.today(), widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    start_date2 = forms.DateField(required=False, initial=date.today() - timedelta(days=60), widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    end_date2 = forms.DateField(required=False, initial=date.today() - timedelta(days=30), widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
