from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import is_valid_path

from mozillians.common.middleware import safe_query_string


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

        if (
            response.status_code == 404
            and not request.path_info.startswith("/u/")
            and not is_valid_path(request.path_info)
            and User.objects.filter(username__iexact=request.path_info[1:].strip("/")).exists()
            and request.user.is_authenticated
            and request.user.userprofile.is_vouched
        ):

            newurl = "/u" + request.path_info
            if request.GET:
                with safe_query_string(request):
                    newurl += "?" + request.META["QUERY_STRING"]
            return HttpResponseRedirect(newurl)
        return response
