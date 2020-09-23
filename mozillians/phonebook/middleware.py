import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import is_valid_path, reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from mozillians.common.middleware import safe_query_string
from mozillians.common.templatetags.helpers import redirect


class UsernameRedirectionMiddleware(object):
    """
    Redirect requests for user profiles from /<username> to
    /u/<username> to avoid breaking profile urls with the new url
    schema.

    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (response.status_code == 404 and not
            request.path_info.startswith('/u/')
            and not is_valid_path(request.path_info)
            and User.objects.filter(username__iexact=request.path_info[1:].strip('/')).exists()
            and request.user.is_authenticated()
                and request.user.userprofile.is_vouched):

            newurl = '/u' + request.path_info
            if request.GET:
                with safe_query_string(request):
                    newurl += '?' + request.META['QUERY_STRING']
            return HttpResponseRedirect(newurl)
        return response
