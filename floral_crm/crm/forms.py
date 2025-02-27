from django import forms
from .models import Customer, Contact, Salesperson
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'estimated_yearly_sales']

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'phone', 'email', 'relationship_score', 'customer']

class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    phone = PhoneNumberField(
        widget=PhoneNumberPrefixWidget(widgets=["US"]),  # Ensure proper initialization
        required=True, 
        help_text='Required. Select country code and enter a valid phone number.'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            Salesperson.objects.create(user=user, phone=self.cleaned_data['phone'])
        return user