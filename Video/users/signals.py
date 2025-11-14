from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from . import models

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a profile for new users."""
    if created:
        models.Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the profile whenever the user object is saved."""
    instance.profile.save()