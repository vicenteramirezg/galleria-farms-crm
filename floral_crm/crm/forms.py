from django import forms
from .models import Customer, Contact, Salesperson, Role
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

import logging

logger = logging.getLogger(__name__)

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'estimated_yearly_sales', 'department']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the logged-in user
        super().__init__(*args, **kwargs)

        # If the user is an Executive, show a dropdown for assigning Salesperson
        if user and user.profile.role == "Executive":
            self.fields['salesperson'] = forms.ModelChoiceField(
                queryset=Salesperson.objects.all(),
                required=True,
                label="Assign Salesperson"
            )

    def clean_estimated_yearly_sales(self):
        sales = self.cleaned_data.get('estimated_yearly_sales')

        logger.info(f"🧐 Raw input before cleaning: {sales} (Type: {type(sales)})")

        if isinstance(sales, str):  # Remove commas only if it's a string
            try:
                sales = int(sales.replace(",", ""))  # Convert to integer
            except ValueError:
                raise forms.ValidationError("Enter a valid whole number.")

        if isinstance(sales, float):  # Prevent decimal inputs
            sales = int(sales)

        logger.info(f"✅ Cleaned value: {sales} (Type: {type(sales)})")

        return sales

    def clean_name(self):
        name = self.cleaned_data.get('name')

        # Check if a customer with the same name already exists (case insensitive)
        if Customer.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("A customer with this name already exists.")

        return name

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['customer', 'name', 'phone', 'email', 'address', 'birthday_month', 'birthday_day', 'relationship_score']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # ✅ Get logged-in user
        super().__init__(*args, **kwargs)

        # ✅ Use the choices from the model
        self.fields["birthday_month"].widget = forms.Select(choices=Contact.MONTHS)
        self.fields["birthday_day"].widget = forms.NumberInput(attrs={"type": "number", "min": 1, "max": 31})

        # ✅ Ensure correct customer filtering
        if user and hasattr(user, 'profile') and user.profile.role == "Salesperson":
            self.fields["customer"].queryset = Customer.objects.filter(salesperson=user.salesperson)
        else:
            self.fields["customer"].queryset = Customer.objects.all()

        # ✅ Pre-fill existing values if available
        if self.instance and self.instance.pk:
            self.fields["birthday_month"].initial = self.instance.birthday_month
            self.fields["birthday_day"].initial = self.instance.birthday_day
            self.fields["customer"].disabled = True  # 🔒 Make customer non-editable when editing a contact

        # Apply Bootstrap classes & center alignment
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control text-center"})  # Centers text inside fields

        # Specifically control width for Address field
        self.fields["address"].widget.attrs.update({"style": "max-width: 400px; margin: 0 auto; max-height: 100px"})  # Centered & fixed width

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