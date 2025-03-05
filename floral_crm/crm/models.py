from django.db import models
from django.contrib.auth.models import User

class Role(models.TextChoices):
    SALESPERSON = 'Salesperson', 'Salesperson'
    EXECUTIVE = 'Executive', 'Executive'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.SALESPERSON)

    def is_executive(self):
        return self.role == Role.EXECUTIVE

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role}"

class Salesperson(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='salesperson')
    phone = models.CharField(max_length=20, blank=True)  # Store phone as a string

    def __str__(self):
        return f"{self.user.get_full_name()}"

class Customer(models.Model):
    MASS_MARKET = 'mass_market'
    MM2 = 'mm2'
    ECOMMERCE = 'ecommerce'
    WHOLESALE = 'wholesale'

    DEPARTMENT_CHOICES = [
        (MASS_MARKET, 'Mass Market'),
        (MM2, 'MM2'),
        (ECOMMERCE, 'Ecommerce'),
        (WHOLESALE, 'Wholesale'),
    ]

    name = models.CharField(max_length=255, unique=True)
    estimated_yearly_sales = models.IntegerField()
    salesperson = models.ForeignKey(Salesperson, on_delete=models.CASCADE, related_name='customers')
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        default=MASS_MARKET
    )

    def get_department_display(self):
        """ Returns the human-readable department name instead of the stored value """
        return dict(self.DEPARTMENT_CHOICES).get(self.department, "No Department")

    def __str__(self):
        return f"{self.name} - {self.get_department_display()}"

class Contact(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='contacts')
    relationship_score = models.IntegerField(default=0)
    birthday = models.DateField(null=True, blank=True)

    def whatsapp_format(self):
        # Remove all non-numeric characters
        cleaned_number = ''.join(filter(str.isdigit, self.phone))
        
        # Ensure the number starts with a country code (e.g., '1' for US/Canada)
        if not cleaned_number.startswith('+'):
            cleaned_number = f"+1{cleaned_number}"  # Adjust the country code as needed
        
        return cleaned_number

    def __str__(self):
        return self.name
