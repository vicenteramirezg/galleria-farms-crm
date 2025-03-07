from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import importlib

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile_and_salesperson(sender, instance, created, **kwargs):
    if created:
        models = importlib.import_module("crm.models")  # Lazy import models to prevent circular import
        Profile = models.Profile
        Role = models.Role
        Salesperson = models.Salesperson

        Profile.objects.create(user=instance, role=Role.SALESPERSON)
        Salesperson.objects.create(user=instance, phone="")  # Placeholder phone

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    models = importlib.import_module("crm.models")  # Lazy import to prevent circular import
    Profile = models.Profile

    instance.profile.save()
