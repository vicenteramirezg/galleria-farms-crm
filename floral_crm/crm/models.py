from django.db import models
from django.contrib.auth.models import User

class Salesperson(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Additional fields for salesperson (if needed)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.get_full_name()

class Customer(models.Model):
    name = models.CharField(max_length=255)
    estimated_yearly_sales = models.DecimalField(max_digits=10, decimal_places=2)
    salesperson = models.ForeignKey(Salesperson, on_delete=models.CASCADE, related_name='customers')

    def __str__(self):
        return self.name

class Contact(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='contacts')
    relationship_score = models.IntegerField(default=0)  # Example: 0-100

    def __str__(self):
        return self.name