import re
import urllib.request, urllib.parse, urllib.error
from contextlib import contextmanager

from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.encoding import iri_to_uri
from django.utils.translation import activate
from django.utils.translation import ugettext_lazy as _lazy

from mozillians.common import urlresolvers

LOGIN_MESSAGE = _lazy('You must be logged in to continue.')
GET_VOUCHED_MESSAGE = _lazy('You must be vouched to continue.')


@contextmanager
def safe_query_string(request):
    """Turn the QUERY_STRING into a unicode- and ascii-safe string.

    We need unicode so it can be combined with a reversed URL, but it
    has to be ascii to go in a Location header. iri_to_uri seems like
    a good compromise.
    """
    qs = request.META['QUERY_STRING']
    try:
        request.META['QUERY_STRING'] = iri_to_uri(qs)
        yield
    finally:
        request.META['QUERY_STRING'] = qs


class LocaleURLMiddleware(object):
    """
    1. Search for the locale.
    2. Save it in the request.
    3. Strip them from the URL.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        request.locale = settings.LANGUAGE_CODE
        activate(settings.LANGUAGE_CODE)

        for view_url in settings.EXEMPT_L10N_URLS:
            if re.search(view_url, request.path):
                return self.get_response(request)

        prefixer = urlresolvers.Prefixer(request)
        urlresolvers.set_url_prefix(prefixer)
        full_path = prefixer.fix(prefixer.shortened_path)

        if full_path != request.path:
            query_string = request.META.get('QUERY_STRING', '')
            full_path = urllib.parse.quote(full_path.encode('utf-8'))

            if query_string:
                full_path = '%s?%s' % (full_path, query_string)

            response = HttpResponsePermanentRedirect(full_path)

            # Vary on Accept-Language if we changed the locale
            old_locale = prefixer.locale
            new_locale, _ = urlresolvers.split_path(full_path)
            if old_locale != new_locale:
                response['Vary'] = 'Accept-Language'

            return response

        request.path_info = '/' + prefixer.shortened_path
        request.locale = prefixer.locale or settings.LANGUAGE_CODE
        activate(prefixer.locale or settings.LANGUAGE_CODE)
        return self.get_response(request)


class HSTSPreloadMiddleware(object):
    """Add header to enable HSTS preload."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        sts_header_name = 'strict-transport-security'
        sts_header = response.get(sts_header_name)

        # Check if HSTS header exists and append preload directive
        if sts_header and settings.ENABLE_HSTS_PRELOAD:
            response[sts_header_name] = sts_header + '; preload'

        return response


class ReferrerPolicyMiddleware(object):
    """Add header to enable Referrer-Policy Header."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        referrer_header_name = 'Referrer-Policy'

        if settings.ENABLE_REFERRER_HEADER:
            response[referrer_header_name] = 'no-referrer'

        return response
