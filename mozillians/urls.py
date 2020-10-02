from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.shortcuts import render
from django.utils.translation import activate
from django.views.static import serve

# Activate a locale so that jinja2 doesn't choke when running a shell
# or individual tests that need translation and don't involve a web
# request, like when testing emails.
activate("en-US")


def error_page(request, template, status=None, **kwargs):
    """Render error templates, found in the root /templates directory.

    If no status parameter is explcitedly passed, this function assumes
    your HTTP status code is the same as your template name (i.e. passing
    a template=404 will render 404.html with the HTTP status code 404).
    """
    return render(request, "%d.html" % template, status=(status or template))


handler404 = lambda r, exc={}: error_page(r, 404, **exc)  # noqa
handler500 = lambda r: error_page(r, 500)  # noqa
handler_csrf = lambda r, cb=None: error_page(r, "csrf_error", status=400)  # noqa


urlpatterns = [
    url(r"^oidc/", include("mozilla_django_oidc.urls")),
    url(r"", include("mozillians.phonebook.urls", namespace="phonebook")),
    # Admin URLs.
    url(r"^admin/", admin.site.urls),
]

admin.site.site_header = "Mozillians Administration"
admin.site.site_title = "Mozillians"

# In DEBUG mode, serve media files through Django, and serve error pages
# via predictable routes. Add in qunit tests.
if settings.DEBUG:
    # Remove leading and trailing slashes so the regex matches.
    urlpatterns += [
        # Add the 404, 500, and csrf pages for testing
        url(r"^404/$", handler404),
        url(r"^500/$", handler500),
        url(r"^csrf/$", handler_csrf),
        url(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
