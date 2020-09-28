from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import logout as auth_logout
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

import mozillians.phonebook.forms as forms
from mozillians.common.decorators import allow_public, allow_unvouched
from mozillians.common.middleware import GET_VOUCHED_MESSAGE, LOGIN_MESSAGE
from mozillians.common.templatetags.helpers import (get_object_or_none,
                                                    redirect, urlparams)
from mozillians.common.urlresolvers import reverse
from mozillians.users.managers import EMPLOYEES, MOZILLIANS, PRIVATE, PUBLIC
from mozillians.users.models import ExternalAccount, IdpProfile, UserProfile

ORIGINAL_CONNECTION_USER_ID = 'https://sso.mozilla.com/claim/original_connection_user_id'


@never_cache
@allow_public
def home(request):
    if request.user.is_authenticated():
        return redirect('phonebook:profile_view', request.user.username)
    return render(request, 'phonebook/home.html')


@allow_public
@never_cache
def view_profile(request, username):
    """View a profile by username."""
    data = {}
    privacy_mappings = {'anonymous': PUBLIC, 'mozillian': MOZILLIANS, 'employee': EMPLOYEES,
                        'private': PRIVATE, 'myself': None}
    privacy_level = None

    if (request.user.is_authenticated() and request.user.username == username):
        # own profile
        view_as = request.GET.get('view_as', 'myself')
        privacy_level = privacy_mappings.get(view_as, None)
        profile = UserProfile.objects.privacy_level(privacy_level).get(user__username=username)
        data['privacy_mode'] = view_as
    else:
        userprofile_query = UserProfile.objects.filter(user__username=username)
        public_profile_exists = userprofile_query.public().exists()
        profile_exists = userprofile_query.exists()
        profile_complete = userprofile_query.exclude(full_name='').exists()

        if not public_profile_exists:
            if not request.user.is_authenticated():
                # you have to be authenticated to continue
                messages.warning(request, LOGIN_MESSAGE)
                return (login_required(view_profile, login_url=reverse('phonebook:home'))
                        (request, username))

            if not request.user.userprofile.is_vouched:
                # you have to be vouched to continue
                messages.error(request, GET_VOUCHED_MESSAGE)
                return redirect('phonebook:home')

        if not profile_exists or not profile_complete:
            raise Http404

        profile = UserProfile.objects.get(user__username=username)
        profile.set_instance_privacy_level(PUBLIC)
        if request.user.is_authenticated():
            profile.set_instance_privacy_level(
                request.user.userprofile.privacy_level)

    data['shown_user'] = profile.user
    data['profile'] = profile
    data['primary_identity'] = profile.identity_profiles.filter(primary_contact_identity=True)
    data['alternate_identities'] = profile.identity_profiles.filter(primary_contact_identity=False)

    return render(request, 'phonebook/profile.html', data)


@allow_unvouched
@never_cache
def edit_profile(request):
    """Edit user profile view."""
    # Don't use request.user
    user = User.objects.get(pk=request.user.id)
    profile = user.userprofile
    sections = {
        'basic_section': ['user_form', 'basic_information_form'],
    }

    curr_sect = next((s for s in sections.keys() if s in request.POST), None)

    def get_request_data(form):
        if curr_sect and form in sections[curr_sect]:
            return request.POST
        return None

    ctx = {}
    ctx['user_form'] = forms.UserForm(get_request_data('user_form'), instance=user)
    basic_information_data = get_request_data('basic_information_form')
    ctx['basic_information_form'] = forms.BasicInformationForm(basic_information_data,
                                                               request.FILES or None,
                                                               instance=profile)

    forms_valid = True
    if request.POST:
        if not curr_sect:
            raise Http404
        curr_forms = map(lambda x: ctx[x], sections[curr_sect])
        forms_valid = all(map(lambda x: x.is_valid(), curr_forms))
        if forms_valid:
            old_username = request.user.username
            for f in curr_forms:
                f.save()

            next_section = request.GET.get('next')
            next_url = urlparams(reverse('phonebook:profile_edit'), next_section)
            if user.username != old_username:
                msg = _(u'You changed your username; '
                        u'please note your profile URL has also changed.')
                messages.info(request, _(msg))
            return HttpResponseRedirect(next_url)

    ctx.update({
        'profile': request.user.userprofile,
        'vouch_threshold': settings.CAN_VOUCH_THRESHOLD,
        'forms_valid': forms_valid
    })

    return render(request, 'phonebook/edit_profile.html', ctx)


@allow_unvouched
@never_cache
def delete_identity(request, identity_pk):
    """Delete alternate email address."""
    user = User.objects.get(pk=request.user.id)
    profile = user.userprofile

    # Only email owner can delete emails
    idp_query = IdpProfile.objects.filter(profile=profile, pk=identity_pk)
    if not idp_query.exists():
        raise Http404()

    idp_query = idp_query.filter(primary=False, primary_contact_identity=False)
    if idp_query.exists():
        idp_type = idp_query[0].get_type_display()
        idp_query.delete()
        msg = _(u'Identity {0} successfully deleted.'.format(idp_type))
        messages.success(request, msg)
        return redirect('phonebook:profile_edit')

    # We are trying to delete the primary identity, politely ignore the request
    msg = _(u'Sorry the requested Identity cannot be deleted.')
    messages.error(request, msg)
    return redirect('phonebook:profile_edit')


@allow_unvouched
@never_cache
def confirm_delete(request):
    """Display a confirmation page asking the user if they want to
    leave.

    """
    return render(request, 'phonebook/confirm_delete.html')


@allow_unvouched
@never_cache
@require_POST
def delete(request):
    request.user.delete()
    messages.info(request, _('Your account has been deleted. Thanks for being a Mozillian!'))
    return logout(request)


@allow_unvouched
def logout(request):
    """View that logs out the user and redirects to home page."""
    auth_logout(request)
    return redirect('phonebook:home')


@allow_unvouched
@never_cache
def delete_idp_profiles(request):
    """QA helper: Delete IDP profiles for request.user"""
    request.user.userprofile.idp_profiles.all().delete()
    messages.warning(request, 'Identities deleted.')
    return redirect('phonebook:profile_edit')
