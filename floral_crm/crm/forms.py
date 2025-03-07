from django import forms
from .models import Customer, Contact, Salesperson, Role
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

import logging

logger = logging.getLogger(__name__)

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'estimated_yearly_sales', 'department']  # Salesperson added dynamically for Executives

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the logged-in user
        super().__init__(*args, **kwargs)

        if user and hasattr(user, "profile"):
            if user.profile.role == "Executive":
                # ✅ Executives can assign a salesperson
                self.fields['salesperson'] = forms.ModelChoiceField(
                    queryset=Salesperson.objects.all(),
                    required=True,
                    label="Assign Salesperson"
                )

                # ✅ Prefill the salesperson field if editing an existing customer
                if self.instance.pk and self.instance.salesperson:
                    self.fields['salesperson'].initial = self.instance.salesperson

            elif user.profile.role == "Salesperson":
                # 🚫 Salespersons should NOT modify their assigned salesperson
                salesperson_queryset = Salesperson.objects.filter(user=user)

                # ✅ Only set salesperson if the instance exists
                salesperson_initial = self.instance.salesperson if self.instance.pk else user.salesperson

                self.fields['salesperson'] = forms.ModelChoiceField(
                    queryset=salesperson_queryset,
                    initial=salesperson_initial,
                    required=False,
                    label="Salesperson",
                    widget=forms.Select(attrs={'readonly': 'readonly', 'disabled': 'disabled'})  # Prevent modifications
                )

    def clean_salesperson(self):
        """ Ensure Salespeople cannot modify the assigned salesperson. """
        if self.instance.pk and self.instance.salesperson and self.cleaned_data.get("salesperson") != self.instance.salesperson:
            return self.instance.salesperson  # ✅ Return existing salesperson to bypass validation
        return self.cleaned_data.get("salesperson")

    def clean_estimated_yearly_sales(self):
        """ Clean and validate the estimated yearly sales field. """
        sales = self.cleaned_data.get('estimated_yearly_sales')

        if isinstance(sales, str):  # Remove commas only if it's a string
            try:
                sales = int(sales.replace(",", ""))  # Convert to integer
            except ValueError:
                raise forms.ValidationError("Enter a valid whole number.")

        if isinstance(sales, float):  # Prevent decimal inputs
            sales = int(sales)

        return sales

    def clean_name(self):
        """ Ensure customer names are unique. """
        name = self.cleaned_data.get('name')

        if Customer.objects.filter(name__iexact=name).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("A customer with this name already exists.")

        return name

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['customer', 'name', 'phone', 'email', 'address', 'birthday_month', 'birthday_day', 'relationship_score']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # ✅ Get the logged-in user
        super().__init__(*args, **kwargs)

        # ✅ Use the choices from the model
        self.fields["birthday_month"].widget = forms.Select(choices=Contact.MONTHS)
        self.fields["birthday_day"].widget = forms.NumberInput(attrs={"type": "number", "min": 1, "max": 31})

        # ✅ Ensure correct customer filtering
        if user and hasattr(user, 'profile'):
            if user.profile.role == "Executive":
                self.fields["customer"].queryset = Customer.objects.all()  # ✅ Executives see all customers
            elif user.profile.role == "Salesperson":
                self.fields["customer"].queryset = Customer.objects.filter(salesperson=user.salesperson)  # ✅ Salespersons see only their customers
            elif "Manager" in user.profile.role:
                department = user.profile.role.replace("Manager - ", "")  # Extract department
                self.fields["customer"].queryset = Customer.objects.filter(department__iexact=department)  # ✅ Managers see customers in their department

        # ✅ If editing an existing contact, keep customer selection locked
        if self.instance and self.instance.pk:
            self.fields["customer"].disabled = True  # 🔒 Keep customer non-editable when editing a contact

        # ✅ Apply Bootstrap styling
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control text-center"})  # Centers text inside fields

        # ✅ Specifically control width for Address field
        self.fields["address"].widget.attrs.update({"style": "max-width: 400px; margin: 0 auto; max-height: 100px"})
        
class SignupForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    phone = forms.CharField(
        max_length=20,  # Store country code + number
        required=True,
        help_text='Required. Enter a valid phone number including country code.',
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone', 'password1', 'password2']

    def clean_username(self):
        """ Ensure username is a valid email address """
        username = self.cleaned_data['username']
        if "@" not in username:
            raise forms.ValidationError("Please enter a valid email address.")
        return username.lower()

    def clean_phone(self):
        phone_number = self.cleaned_data['phone']
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"
        return phone_number  # Ensures phone is always stored with "+"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = user.username  # ✅ Store the username as the email
        if commit:
            user.save()  # Save user first so signal can trigger

            # ✅ Wait for signal to create Salesperson, then update the phone
            from crm.models import Salesperson  # Import inside method to prevent circular import
            salesperson = getattr(user, "salesperson", None)  # Get Salesperson if it exists
            if salesperson:  # Update phone only if Salesperson exists
                salesperson.phone = self.cleaned_data["phone"]
                salesperson.save()

        return user