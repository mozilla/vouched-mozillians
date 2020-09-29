import re

import happyforms
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _lazy

from mozillians.phonebook.validators import validate_username
from mozillians.users.models import UserProfile

REGEX_NUMERIC = re.compile(r'\d+', re.IGNORECASE)


class UserForm(happyforms.ModelForm):
    """Instead of just inhereting form a UserProfile model form, this
    base class allows us to also abstract over methods that have to do
    with the User object that need to exist in both Registration and
    Profile.

    """
    username = forms.CharField(label=_lazy('Username'))

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
            raise forms.ValidationError(_('This username is in use. Please try'
                                          ' another.'))

        # No funky characters in username.
        if not re.match(r'^[\w.@+-]+$', username):
            raise forms.ValidationError(_('Please use only alphanumeric'
                                          ' characters'))

        if not validate_username(username):
            raise forms.ValidationError(_('This username is not allowed, '
                                          'please choose another.'))
        return username


class BasicInformationForm(happyforms.ModelForm):

    class Meta:
        model = UserProfile
        fields = ('full_name', 'privacy_full_name',)
        widgets = {'bio': forms.Textarea()}
