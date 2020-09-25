import re
from datetime import datetime

import happyforms
from django import forms
from django.contrib.auth.models import User
from django.forms.models import BaseInlineFormSet, inlineformset_factory
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy

from mozillians.phonebook.validators import validate_username
from mozillians.phonebook.widgets import MonthYearWidget
from mozillians.users.models import (ExternalAccount, IdpProfile,
                                     UserProfile)

REGEX_NUMERIC = re.compile(r'\d+', re.IGNORECASE)


class ExternalAccountForm(happyforms.ModelForm):
    class Meta:
        model = ExternalAccount
        fields = ['type', 'identifier', 'privacy']

    def clean(self):
        cleaned_data = super(ExternalAccountForm, self).clean()
        identifier = cleaned_data.get('identifier')
        account_type = cleaned_data.get('type')

        if account_type and identifier:
            # If the Account expects an identifier and user provided a
            # full URL, try to extract the identifier from the URL.
            url = ExternalAccount.ACCOUNT_TYPES[account_type].get('url')
            if url and identifier.startswith('http'):
                url_pattern_re = url.replace('{identifier}', '(.+)')
                identifier = identifier.rstrip('/')
                url_pattern_re = url_pattern_re.rstrip('/')
                match = re.match(url_pattern_re, identifier)
                if match:
                    identifier = match.groups()[0]

            validator = ExternalAccount.ACCOUNT_TYPES[account_type].get('validator')
            if validator:
                identifier = validator(identifier)

            cleaned_data['identifier'] = identifier

        return cleaned_data


AccountsFormset = inlineformset_factory(UserProfile, ExternalAccount,
                                        form=ExternalAccountForm, extra=1)


class IdpProfileForm(happyforms.ModelForm):
    """Form for the IdpProfile model."""

    class Meta:
        model = IdpProfile
        fields = ['privacy']


IdpProfileFormset = inlineformset_factory(UserProfile, IdpProfile,
                                          form=IdpProfileForm, extra=0)


class EmailPrivacyForm(happyforms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['privacy_email']


class UserForm(happyforms.ModelForm):
    """Instead of just inhereting form a UserProfile model form, this
    base class allows us to also abstract over methods that have to do
    with the User object that need to exist in both Registration and
    Profile.

    """
    username = forms.CharField(label=_lazy(u'Username'))

    class Meta:
        model = User
        fields = ['username']

    def clean_username(self):
        username = self.cleaned_data['username']
        if not username:
            return self.instance.username

        # Don't be jacking somebody's username
        # This causes a potential race condition however the worst that can
        # happen is bad UI.
        if (User.objects.filter(username=username).
                exclude(pk=self.instance.id).exists()):
            raise forms.ValidationError(_(u'This username is in use. Please try'
                                          u' another.'))

        # No funky characters in username.
        if not re.match(r'^[\w.@+-]+$', username):
            raise forms.ValidationError(_(u'Please use only alphanumeric'
                                          u' characters'))

        if not validate_username(username):
            raise forms.ValidationError(_(u'This username is not allowed, '
                                          u'please choose another.'))
        return username


class BasicInformationForm(happyforms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ('full_name', 'privacy_full_name',)
        widgets = {'bio': forms.Textarea()}


class ContributionForm(happyforms.ModelForm):
    date_mozillian = forms.DateField(
        required=False,
        label=_lazy(u'When did you get involved with Mozilla?'),
        widget=MonthYearWidget(years=range(1998, datetime.today().year + 1),
                               required=False))

    class Meta:
        model = UserProfile
        fields = ('date_mozillian', 'privacy_date_mozillian',)

class EmailForm(happyforms.Form):
    email = forms.EmailField(label=_lazy(u'Email'))

    def clean_email(self):
        email = self.cleaned_data['email']
        if (User.objects.exclude(pk=self.initial['user_id']).filter(email=email).exists()):
            raise forms.ValidationError(_(u'Email is currently associated with another user.'))
        return email

    def email_changed(self):
        return self.cleaned_data['email'] != self.initial['email']
