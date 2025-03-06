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
    MONTHS = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"),
        (5, "May"), (6, "June"), (7, "July"), (8, "August"),
        (9, "September"), (10, "October"), (11, "November"), (12, "December")
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    birthday_month = models.IntegerField(choices=MONTHS, blank=True, null=True)
    birthday_day = models.IntegerField(blank=True, null=True)
    relationship_score = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=3)

    def __str__(self):
        return f"{self.name} ({self.customer.name})"