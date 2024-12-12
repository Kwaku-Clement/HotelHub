from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Users

class BaseFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control",
                "placeholder": field.label
            })

class LoginForm(BaseFormMixin, forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class ChangePasswordForm(BaseFormMixin, PasswordChangeForm):
    pass

class UserRegistrationForm(BaseFormMixin, UserCreationForm):
    class Meta:
        model = Users
        fields = ['first_name', 'last_name', 'username', 'role', 'phone', 'address', 'password1', 'password2']
