from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import Salesperson, Profile, Role

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile_and_salesperson(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance, role=Role.SALESPERSON)
        Salesperson.objects.create(user=instance, phone="")  # Placeholder phone

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()