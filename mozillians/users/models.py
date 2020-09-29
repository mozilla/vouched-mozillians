import logging
import os
import uuid
from itertools import chain

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Manager, ManyToManyField
from django.utils.encoding import iri_to_uri
from django.utils.http import urlquote
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy
from product_details import product_details

from mozillians.common.urlresolvers import reverse
from mozillians.phonebook.validators import validate_email
from mozillians.users.managers import (EMPLOYEES, MOZILLIANS, PRIVACY_CHOICES,
                                       PRIVACY_CHOICES_WITH_PRIVATE, PRIVATE,
                                       PUBLIC, PUBLIC_INDEXABLE_FIELDS,
                                       UserProfileQuerySet)

COUNTRIES = product_details.get_regions('en-US')
AVATAR_SIZE = (300, 300)
logger = logging.getLogger(__name__)
ProfileManager = Manager.from_queryset(UserProfileQuerySet)


def _calculate_photo_filename(instance, filename):
    """Generate a unique filename for uploaded photo."""
    return os.path.join(settings.USER_AVATAR_DIR, str(uuid.uuid4()) + '.jpg')


class PrivacyField(models.PositiveSmallIntegerField):

    def __init__(self, *args, **kwargs):
        myargs = {'default': MOZILLIANS,
                  'choices': PRIVACY_CHOICES}
        myargs.update(kwargs)
        super(PrivacyField, self).__init__(*args, **myargs)


class UserProfilePrivacyModel(models.Model):
    _privacy_level = None

    privacy_full_name = PrivacyField()
    privacy_email = PrivacyField(choices=PRIVACY_CHOICES_WITH_PRIVATE,
                                 default=MOZILLIANS)
    privacy_date_mozillian = PrivacyField()
    privacy_title = PrivacyField()

    CACHED_PRIVACY_FIELDS = None

    class Meta:
        abstract = True

    @classmethod
    def clear_privacy_fields_cache(cls):
        """
        Clear any caching of the privacy fields.
        (This is only used in testing.)
        """
        cls.CACHED_PRIVACY_FIELDS = None

    @classmethod
    def privacy_fields(cls):
        """
        Return a dictionary whose keys are the names of the fields in this
        model that are privacy-controlled, and whose values are the default
        values to use for those fields when the user is not privileged to
        view their actual value.

        Note: should be only used through UserProfile . We should
        fix this.

        """
        # Cache on the class object
        if cls.CACHED_PRIVACY_FIELDS is None:
            privacy_fields = {}
            field_names = list(set(chain.from_iterable(
                (field.name, field.attname) if hasattr(field, 'attname') else
                (field.name,) for field in cls._meta.get_fields()
                if not (field.many_to_one and field.related_model is None)
            )))
            for name in field_names:
                if name.startswith('privacy_') or not 'privacy_%s' % name in field_names:
                    # skip privacy fields and uncontrolled fields
                    continue
                field = cls._meta.get_field(name)
                # Okay, this is a field that is privacy-controlled
                # Figure out a good default value for it (to show to users
                # who aren't privileged to see the actual value)
                if isinstance(field, ManyToManyField):
                    default = field.remote_field.model.objects.none()
                else:
                    default = field.get_default()
                privacy_fields[name] = default
            # HACK: There's not really an email field on UserProfile,
            # but it's faked with a property
            privacy_fields['email'] = ''

            cls.CACHED_PRIVACY_FIELDS = privacy_fields
        return cls.CACHED_PRIVACY_FIELDS


class UserProfile(UserProfilePrivacyModel):
    objects = ProfileManager()

    user = models.OneToOneField(User)
    full_name = models.CharField(max_length=255, default='', blank=False,
                                 verbose_name=_lazy('Full Name'))
    is_vouched = models.BooleanField(
        default=False,
        help_text='You can edit vouched status by editing invidual vouches')
    can_vouch = models.BooleanField(
        default=False,
        help_text='You can edit can_vouch status by editing invidual vouches')
    last_updated = models.DateTimeField(auto_now=True)

    date_mozillian = models.DateField('When was involved with Mozilla',
                                      null=True, blank=True, default=None)
    # This is the Auth0 user ID. We are saving only the primary here.
    auth0_user_id = models.CharField(max_length=1024, default='', blank=True)
    is_staff = models.BooleanField(default=False)

    def __unicode__(self):
        """Return this user's name when their profile is called."""
        return self.display_name

    def get_absolute_url(self):
        return reverse('phonebook:profile_view', args=[self.user.username])

    class Meta:
        db_table = 'profile'
        ordering = ['full_name']

    def __getattribute__(self, attrname):
        """Special privacy aware __getattribute__ method.

        This method returns the real value of the attribute of object,
        if the privacy_level of the attribute is at least as large as
        the _privacy_level attribute.

        Otherwise it returns a default privacy respecting value for
        the attribute, as defined in the privacy_fields dictionary.

        special_functions provides methods that privacy safe their
        respective properties, where the privacy modifications are
        more complex.
        """
        _getattr = (lambda x: super(UserProfile, self).__getattribute__(x))
        privacy_fields = UserProfile.privacy_fields()
        privacy_level = _getattr('_privacy_level')
        special_functions = {
            'accounts': '_accounts',
            'alternate_emails': '_alternate_emails',
            'email': '_primary_email',
            'is_public_indexable': '_is_public_indexable',
            'vouches_made': '_vouches_made',
            'vouches_received': '_vouches_received',
            'vouched_by': '_vouched_by',
            'identity_profiles': '_identity_profiles'
        }

        if attrname in special_functions:
            return _getattr(special_functions[attrname])

        if not privacy_level or attrname not in privacy_fields:
            return _getattr(attrname)

        field_privacy = _getattr('privacy_%s' % attrname)
        if field_privacy < privacy_level:
            return privacy_fields.get(attrname)

        return _getattr(attrname)

    def _filter_accounts_privacy(self, accounts):
        if self._privacy_level:
            return accounts.filter(privacy__gte=self._privacy_level)
        return accounts

    @property
    def _accounts(self):
        _getattr = (lambda x: super(UserProfile, self).__getattribute__(x))
        excluded_types = [ExternalAccount.TYPE_WEBSITE, ExternalAccount.TYPE_EMAIL]
        accounts = _getattr('externalaccount_set').exclude(type__in=excluded_types)
        return self._filter_accounts_privacy(accounts)

    @property
    def _alternate_emails(self):
        _getattr = (lambda x: super(UserProfile, self).__getattribute__(x))
        accounts = _getattr('externalaccount_set').filter(type=ExternalAccount.TYPE_EMAIL)
        return self._filter_accounts_privacy(accounts)

    @property
    def _identity_profiles(self):
        _getattr = (lambda x: super(UserProfile, self).__getattribute__(x))
        accounts = _getattr('idp_profiles').all()
        return self._filter_accounts_privacy(accounts)

    @property
    def _is_public_indexable(self):
        for field in PUBLIC_INDEXABLE_FIELDS:
            if getattr(self, field, None) and getattr(self, 'privacy_%s' % field, None) == PUBLIC:
                return True
        return False

    @property
    def _primary_email(self):
        _getattr = (lambda x: super(UserProfile, self).__getattribute__(x))

        privacy_fields = UserProfile.privacy_fields()

        if self._privacy_level:
            # Try IDP contact first
            if self.idp_profiles.exists():
                contact_ids = self.identity_profiles.filter(primary_contact_identity=True)
                if contact_ids.exists():
                    return contact_ids[0].email
                return ''

            # Fallback to user.email
            if _getattr('privacy_email') < self._privacy_level:
                return privacy_fields['email']

        # In case we don't have a privacy aware attribute access
        if self.idp_profiles.filter(primary_contact_identity=True).exists():
            return self.idp_profiles.filter(primary_contact_identity=True)[0].email
        return _getattr('user').email

    @property
    def _vouched_by(self):
        privacy_level = self._privacy_level
        voucher = (UserProfile.objects.filter(vouches_made__vouchee=self)
                   .order_by('vouches_made__date'))

        if voucher.exists():
            voucher = voucher[0]
            if privacy_level:
                voucher.set_instance_privacy_level(privacy_level)
                for field in UserProfile.privacy_fields():
                    if getattr(voucher, 'privacy_%s' % field) >= privacy_level:
                        return voucher
                return None
            return voucher

        return None

    def _vouches(self, type):
        _getattr = (lambda x: super(UserProfile, self).__getattribute__(x))

        vouch_ids = []
        for vouch in _getattr(type).all():
            vouch.vouchee.set_instance_privacy_level(self._privacy_level)
            for field in UserProfile.privacy_fields():
                if getattr(vouch.vouchee, 'privacy_%s' % field, 0) >= self._privacy_level:
                    vouch_ids.append(vouch.id)
        vouches = _getattr(type).filter(pk__in=vouch_ids)

        return vouches

    @property
    def _vouches_made(self):
        _getattr = (lambda x: super(UserProfile, self).__getattribute__(x))
        if self._privacy_level:
            return self._vouches('vouches_made')
        return _getattr('vouches_made')

    @property
    def _vouches_received(self):
        _getattr = (lambda x: super(UserProfile, self).__getattribute__(x))
        if self._privacy_level:
            return self._vouches('vouches_received')
        return _getattr('vouches_received')

    @property
    def display_name(self):
        return self.full_name

    @property
    def privacy_level(self):
        """Return user privacy clearance."""
        if self.user.is_superuser:
            return PRIVATE
        if self.groups.filter(name='staff').exists():
            return EMPLOYEES
        if self.is_vouched:
            return MOZILLIANS
        return PUBLIC

    @property
    def is_complete(self):
        """Tests if a user has all the information needed to move on
        past the original registration view.

        """
        return self.display_name.strip() != ''

    @property
    def is_public(self):
        """Return True is any of the privacy protected fields is PUBLIC."""
        # TODO needs update

        for field in type(self).privacy_fields():
            if getattr(self, 'privacy_%s' % field, None) == PUBLIC:
                return True
        return False

    @property
    def is_manager(self):
        return self.user.is_superuser

    @property
    def date_vouched(self):
        """ Return the date of the first vouch, if available."""
        vouches = self.vouches_received.all().order_by('date')[:1]
        if vouches:
            return vouches[0].date
        return None

    def set_instance_privacy_level(self, level):
        """Sets privacy level of instance."""
        self._privacy_level = level

    def set_privacy_level(self, level, save=True):
        """Sets all privacy enabled fields to 'level'."""
        for field in type(self).privacy_fields():
            setattr(self, 'privacy_%s' % field, level)
        if save:
            self.save()

    def is_vouchable(self, voucher):
        """Check whether self can receive a vouch from voucher."""
        # If there's a voucher, they must be able to vouch.
        if voucher and not voucher.can_vouch:
            return False

        # Maximum VOUCH_COUNT_LIMIT vouches per account, no matter what.
        if self.vouches_received.all().count() >= settings.VOUCH_COUNT_LIMIT:
            return False

        # If you've already vouched this account, you cannot do it again
        vouch_query = self.vouches_received.filter(voucher=voucher)
        if voucher and vouch_query.exists():
            return False

        return True

    def save(self, *args, **kwargs):
        self._privacy_level = None
        autovouch = kwargs.pop('autovouch', False)

        super(UserProfile, self).save(*args, **kwargs)
        # Auto_vouch follows the first save, because you can't
        # create foreign keys without a database id.

        if autovouch:
            self.auto_vouch()


class IdpProfile(models.Model):
    """Basic Identity Provider information for Profiles."""
    PROVIDER_UNKNOWN = 0
    PROVIDER_PASSWORDLESS = 10
    PROVIDER_GOOGLE = 20
    PROVIDER_GITHUB = 30
    PROVIDER_FIREFOX_ACCOUNTS = 31
    PROVIDER_LDAP = 40

    PROVIDER_TYPES = (
        (PROVIDER_UNKNOWN, 'Unknown Provider',),
        (PROVIDER_PASSWORDLESS, 'Passwordless Provider',),
        (PROVIDER_GOOGLE, 'Google Provider',),
        (PROVIDER_GITHUB, 'Github Provider',),
        (PROVIDER_FIREFOX_ACCOUNTS, 'Firefox Accounts Provider',),
        (PROVIDER_LDAP, 'LDAP Provider',),

    )
    # High Security OPs
    HIGH_AAL_ACCOUNTS = [PROVIDER_LDAP,
                         PROVIDER_FIREFOX_ACCOUNTS,
                         PROVIDER_GITHUB,
                         PROVIDER_GOOGLE]

    profile = models.ForeignKey(UserProfile, related_name='idp_profiles')
    type = models.IntegerField(choices=PROVIDER_TYPES,
                               default=None,
                               null=True,
                               blank=False)
    # Auth0 required data
    auth0_user_id = models.CharField(max_length=1024, default='', blank=True)
    primary = models.BooleanField(default=False)
    email = models.EmailField(blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    privacy = models.PositiveIntegerField(default=MOZILLIANS, choices=PRIVACY_CHOICES_WITH_PRIVATE)
    primary_contact_identity = models.BooleanField(default=False)
    username = models.CharField(max_length=1024, default='', blank=True)

    def get_provider_type(self):
        """Helper method to autopopulate the model type given the user_id."""
        if 'ad|' in self.auth0_user_id:
            return self.PROVIDER_LDAP

        if 'oauth2|firefoxaccounts' in self.auth0_user_id:
            return self.PROVIDER_FIREFOX_ACCOUNTS

        if 'github|' in self.auth0_user_id:
            return self.PROVIDER_GITHUB

        if 'google-oauth2|' in self.auth0_user_id:
            return self.PROVIDER_GOOGLE

        if 'email|' in self.auth0_user_id:
            return self.PROVIDER_PASSWORDLESS

        return self.PROVIDER_UNKNOWN

    def save(self, *args, **kwargs):
        """Custom save method.

        Provides a default contact identity and a helper to assign the provider type.
        """
        self.type = self.get_provider_type()
        # If there isn't a primary contact identity, create one
        if not (IdpProfile.objects.filter(profile=self.profile,
                                          primary_contact_identity=True).exists()):
            self.primary_contact_identity = True

        super(IdpProfile, self).save(*args, **kwargs)

        # Save profile.privacy_email when a primary contact identity changes
        profile = self.profile
        if self.primary_contact_identity:
            profile.privacy_email = self.privacy
        # Set the user id in the userprofile too
        if self.primary:
            profile.auth0_user_id = self.auth0_user_id
        profile.save()

    def __unicode__(self):
        return '{}|{}|{}'.format(self.profile, self.type, self.email)

    class Meta:
        unique_together = ('profile', 'type', 'email')


class Vouch(models.Model):
    vouchee = models.ForeignKey(UserProfile, related_name='vouches_received')
    voucher = models.ForeignKey(UserProfile, related_name='vouches_made',
                                null=True, default=None, blank=True,
                                on_delete=models.SET_NULL)
    description = models.TextField(max_length=500, verbose_name=_lazy('Reason for Vouching'),
                                   default='')
    autovouch = models.BooleanField(default=False)
    date = models.DateTimeField()

    class Meta:
        verbose_name_plural = 'vouches'
        unique_together = ('vouchee', 'voucher')
        ordering = ['-date']

    def __unicode__(self):
        return '{0} vouched by {1}'.format(self.vouchee, self.voucher)


class UsernameBlacklist(models.Model):
    value = models.CharField(max_length=30, unique=True)
    is_regex = models.BooleanField(default=False)

    def __unicode__(self):
        return self.value

    class Meta:
        ordering = ['value']


class ExternalAccount(models.Model):
    # Constants for type field values.
    TYPE_EMAIL = 'EMAIL'

    # Account type field documentation:
    # name: The name of the service that this account belongs to. What
    #       users see
    # url: If the service features profile pages for its users, then
    #      this field should be a link to that profile page. User's
    #      identifier should be replaced by the special string
    #      {identifier}.
    # validator: Points to a function which will clean and validate
    #            user's entry. Function should return the cleaned
    #            data.
    ACCOUNT_TYPES = {
        TYPE_EMAIL: {'name': 'Alternate email address',
                     'url': '',
                     'validator': validate_email}
    }

    user = models.ForeignKey(UserProfile)
    identifier = models.CharField(max_length=255, verbose_name=_lazy('Account Username'))
    type = models.CharField(max_length=30,
                            choices=sorted([(k, v['name']) for (k, v) in ACCOUNT_TYPES.items()
                                            if k != TYPE_EMAIL], key=lambda x: x[1]),
                            verbose_name=_lazy('Account Type'))
    privacy = models.PositiveIntegerField(default=MOZILLIANS, choices=PRIVACY_CHOICES_WITH_PRIVATE)

    class Meta:
        ordering = ['type']
        unique_together = ('identifier', 'type', 'user')

    def get_identifier_url(self):
        url = self.ACCOUNT_TYPES[self.type]['url'].format(identifier=urlquote(self.identifier))
        if self.type == 'LINKEDIN' and '://' in self.identifier:
            return self.identifier

        return iri_to_uri(url)

    def unique_error_message(self, model_class, unique_check):
        if model_class == type(self) and unique_check == ('identifier', 'type', 'user'):
            return _('You already have an account with this name and type.')
        else:
            return super(ExternalAccount, self).unique_error_message(model_class, unique_check)

    def __unicode__(self):
        return self.type
