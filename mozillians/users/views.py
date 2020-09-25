from functools import reduce
from operator import or_

from dal import autocomplete
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from pytz import country_timezones

from mozillians.common.templatetags.helpers import get_object_or_none
from mozillians.users.models import IdpProfile, UserProfile


class BaseProfileAdminAutocomplete(autocomplete.Select2QuerySetView):
    """Base class for django-autocomplete-light."""

    def get_queryset(self):
        """Base queryset used only in admin.

        Return all the users who have completed their profile registration.
        """
        if not self.request.user.is_staff:
            return UserProfile.objects.none()

        qs = UserProfile.objects.complete()
        self.q_base_filter = (Q(full_name__icontains=self.q)
                              | Q(user__email__icontains=self.q)
                              | Q(user__username__icontains=self.q))

        if self.q:
            qs = qs.filter(self.q_base_filter)
        return qs


class UsersAdminAutocomplete(autocomplete.Select2QuerySetView):
    """Base class for django-autocomplete-light."""

    def get_queryset(self):
        """Base queryset used only in admin.

        Return all the users who have completed their profile registration.
        """
        if not self.request.user.is_staff:
            return User.objects.none()

        qs = User.objects.all()
        self.q_base_filter = (Q(userprofile__full_name__icontains=self.q)
                              | Q(email__icontains=self.q)
                              | Q(username__icontains=self.q))

        if self.q:
            qs = qs.filter(self.q_base_filter)
        return qs


class VoucherAutocomplete(BaseProfileAdminAutocomplete):

    def get_queryset(self):
        """Augment base queryset by returning only users who can vouch."""
        qs = super(VoucherAutocomplete, self).get_queryset().filter(can_vouch=True)

        if self.q:
            qs = qs.filter(self.q_base_filter)
        return qs


class VouchedAutocomplete(BaseProfileAdminAutocomplete):

    def get_queryset(self):
        """Augment base queryset by returning only vouched users."""
        qs = super(VouchedAutocomplete, self).get_queryset().vouched()

        if self.q:
            qs = qs.filter(self.q_base_filter)
        return qs


class StaffProfilesAutocomplete(autocomplete.Select2QuerySetView):

    def get_results(self, context):
        """Modify the text in the results of the group invitation form."""

        results = []
        for result in context['object_list']:
            pk = self.get_result_value(result)
            if not pk:
                continue

            profile = UserProfile.objects.get(pk=pk)
            idp = get_object_or_none(IdpProfile, profile=profile, primary=True)
            text = self.get_result_label(result)

            # Append the email used for login in the autocomplete text
            if idp:
                text += ' ({0})'.format(idp.email)

            item = {
                'id': pk,
                'text': text
            }
            results.append(item)
        return results

    def get_queryset(self):
        if not self.request.user.userprofile.is_vouched:
            return UserProfile.objects.none()

        queries = []

        # Query staff profiles
        for domain in settings.AUTO_VOUCH_DOMAINS:
            pks = IdpProfile.objects.filter(
                email__endswith='@' + domain).values_list('profile__pk', flat=True)
            queries.append(Q(pk__in=pks))

        query = reduce(or_, queries)

        qs = UserProfile.objects.filter(query).distinct()
        if self.q:
            qs = qs.filter(Q(full_name__icontains=self.q)
                           | Q(user__email__icontains=self.q)
                           | Q(user__username__icontains=self.q))
        return qs
