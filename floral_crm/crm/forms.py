from django import forms
from .models import Customer, Contact
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

import logging

logger = logging.getLogger(__name__)

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'estimated_yearly_sales']

    def clean_estimated_yearly_sales(self):
        sales = self.cleaned_data.get('estimated_yearly_sales')
        
        logger.info(f"🧐 Raw input before cleaning: {sales} (Type: {type(sales)})")

        if isinstance(sales, str):  # Remove commas only if it's a string
            try:
                sales = int(sales.replace(",", ""))  # Convert to integer
            except ValueError:
                raise forms.ValidationError("Enter a valid number.")

        logger.info(f"✅ Cleaned value: {sales} (Type: {type(sales)})")

        return sales

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'phone', 'email', 'relationship_score', 'birthday']
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        salesperson = kwargs.pop('salesperson', None)
        super().__init__(*args, **kwargs)
        if salesperson:
            self.fields['customer'].queryset = Customer.objects.filter(salesperson=salesperson)

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = phone.strip().replace(" ", "").replace("-", "")  # Ensure no spaces or dashes
            if not phone.startswith('+'):
                raise forms.ValidationError("Phone number must be in international format (e.g., +17868755569).")
        return phone

class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    phone = forms.CharField(
        max_length=20,  # To store country code + number as a string
        required=True,
        help_text='Required. Enter a valid phone number including country code.',
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        phone_number = self.cleaned_data['phone']  # Ensure phone is correctly extracted
        if commit:
            user.save()
            user.salesperson.phone = phone_number  # Save phone to the Salesperson model
            user.salesperson.save()
        return user