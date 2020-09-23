import json
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import signals
from django.dispatch import receiver
from mozillians.groups.models import Group
from mozillians.users.models import UserProfile, Vouch
from raven.contrib.django.raven_compat.models import client as sentry_client


# Signal to create a UserProfile.
@receiver(signals.post_save, sender=User, dispatch_uid='create_user_profile_sig')
def create_user_profile(sender, instance, created, raw, **kwargs):
    if not raw:
        up, created = UserProfile.objects.get_or_create(user=instance)
        if not created:
            signals.post_save.send(sender=UserProfile, instance=up, created=created, raw=raw)


# Signal to remove the User object when a profile is deleted
@receiver(signals.post_delete, sender=UserProfile, dispatch_uid='delete_user_obj_sig')
def delete_user_obj_sig(sender, instance, **kwargs):
    with transaction.atomic():
        if instance.user:
            instance.user.delete()


# Signal to remove the UserProfile from all the access groups and update the curator
@receiver(signals.pre_delete, sender=UserProfile,
          dispatch_uid='remove_user_from_access_groups_sig')
def remove_user_from_access_groups(sender, instance, **kwargs):
    """Updates the curators of access groups in case the profile to be deleted

    is a curator.
    """
    groups = Group.objects.filter(is_access_group=True, curators=instance)
    for group in groups:
        # If the user is the only curator of an access group
        # add all the super users as curators and remove the user
        if not group.curator_can_leave(instance):
            for super_user in UserProfile.objects.filter(user__is_superuser=True):
                group.curators.add(super_user)
                if not group.has_member(super_user):
                    group.add_member(super_user)
        group.curators.remove(instance)


# Signals related to vouching.
@receiver(signals.post_delete, sender=Vouch, dispatch_uid='update_vouch_flags_delete_sig')
@receiver(signals.post_save, sender=Vouch, dispatch_uid='update_vouch_flags_save_sig')
def update_vouch_flags(sender, instance, **kwargs):
    if kwargs.get('raw'):
        return
    try:
        profile = instance.vouchee
    except UserProfile.DoesNotExist:
        # In this case we delete not only the vouches but the
        # UserProfile as well. Do nothing.
        return

    vouches_qs = Vouch.objects.filter(vouchee=profile)
    vouches = vouches_qs.count()

    profile.is_vouched = vouches > 0
    profile.can_vouch = vouches >= settings.CAN_VOUCH_THRESHOLD
    profile.save(**{'autovouch': False})
