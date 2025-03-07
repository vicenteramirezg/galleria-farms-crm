from django.db import models
from django.contrib.auth.models import User

class BaseModel(models.Model):
    """ Abstract model to add created/updated timestamps and user tracking """
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set when created
    updated_at = models.DateTimeField(auto_now=True)  # Automatically updated on save
    created_by = models.ForeignKey(User, related_name="%(class)s_created", on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(User, related_name="%(class)s_updated", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True  # Prevents Django from creating a separate table

class Role(models.TextChoices):
    EXECUTIVE = "Executive", "Executive"
    SALESPERSON = "Salesperson", "Salesperson"
    MANAGER_MASS_MARKET = "Manager - Mass Market", "Manager - Mass Market"
    MANAGER_MM2 = "Manager - MM2", "Manager - MM2"
    MANAGER_ECOMMERCE = "Manager - Ecommerce", "Manager - Ecommerce"
    MANAGER_WHOLESALE = "Manager - Wholesale", "Manager - Wholesale"

class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.SALESPERSON)

    def is_executive(self):
        return self.role == Role.EXECUTIVE

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role}"

class Salesperson(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='salesperson')
    phone = models.CharField(max_length=20, blank=True)  # Store phone as a string

    def __str__(self):
        return f"{self.user.get_full_name()}"

class Customer(BaseModel):
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

class Contact(BaseModel):
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

    birthday_month = models.IntegerField(choices=MONTHS, blank=True, null=True)  # ✅ Allow nulls
    birthday_day = models.IntegerField(blank=True, null=True)  # ✅ Allow nulls

    relationship_score = models.IntegerField(
        choices=[(i, i) for i in range(0, 6)],  # ✅ Allow 0 as a choice
        default=0,  # ✅ Ensure the default is 0
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.name} ({self.customer.name})"