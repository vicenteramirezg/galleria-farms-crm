from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Salesperson

User = get_user_model()

@receiver(post_save, sender=User)
def create_salesperson_for_user(sender, instance, created, **kwargs):
    if created:
        Salesperson.objects.create(user=instance)