from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import Salesperson, Profile, Role

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile_and_salesperson(sender, instance, created, **kwargs):
    if created:
        # Create Profile with Salesperson role
        Profile.objects.create(user=instance, role=Role.SALESPERSON)

        # Create Salesperson using user details
        Salesperson.objects.create(
            user=instance,
            phone=""  # User's phone is handled by the form; keep it blank for now
        )