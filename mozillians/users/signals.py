from django.db import transaction
from django.db.models import signals
from django.dispatch import receiver

from mozillians.users.models import UserProfile


# Signal to remove the User object when a profile is deleted
@receiver(signals.post_delete, sender=UserProfile, dispatch_uid='delete_user_obj_sig')
def delete_user_obj_sig(sender, instance, **kwargs):
    with transaction.atomic():
        if instance.user:
            instance.user.delete()
