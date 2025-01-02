from django import forms
from django.utils import timezone

class ReportSelectionForm(forms.Form):
    REPORT_CHOICES = [
        ('store', 'Store Report'),
        ('reservation', 'Reservation Report'),
    ]

    report_type = forms.ChoiceField(
        choices=REPORT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'value': timezone.now().date().strftime('%Y-%m-%d')
        })
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'value': timezone.now().date().strftime('%Y-%m-%d')
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date should be greater than start date.")

        return cleaned_data