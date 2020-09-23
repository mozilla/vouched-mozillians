import json
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import signals
from django.dispatch import receiver
from mozillians.users.models import UserProfile
from raven.contrib.django.raven_compat.models import client as sentry_client


# Signal to remove the User object when a profile is deleted
@receiver(signals.post_delete, sender=UserProfile, dispatch_uid='delete_user_obj_sig')
def delete_user_obj_sig(sender, instance, **kwargs):
    with transaction.atomic():
        if instance.user:
            instance.user.delete()
