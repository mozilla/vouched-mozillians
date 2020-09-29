# -*- coding: utf-8 -*-

# Django settings for the mozillians project.
import json
import os.path
from urllib.parse import urljoin

from decouple import Csv, config
from dj_database_url import parse as db_url
from django_jinja.builtins import DEFAULT_EXTENSIONS
from unipath import Path

PROJECT_MODULE = "mozillians"
# Root path of the project
ROOT = Path(__file__).parent
# Defines the views served for root URLs.
ROOT_URLCONF = "%s.urls" % PROJECT_MODULE
# Absolute path to the directory that holds media.
MEDIA_ROOT = Path("media").resolve()
# URL that handles the media served from MEDIA_ROOT. Make sure to use a
MEDIA_URL = config("MEDIA_URL", default="/media/")
# Absolute path to the directory static files should be collected to.
STATIC_ROOT = Path("static").resolve()
# URL prefix for static files served via whitenoise
STATIC_HOST = config("STATIC_HOST", default="")
# URL prefix for static files.
STATIC_URL = STATIC_HOST + "/static/"

# Application definition
########################
INSTALLED_APPS = (
    # Django contrib apps
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django.contrib.messages",
    "django.contrib.admin",
    # Third-party apps, patches, fixes
    "django_jinja",
    "compressor",
    "django_nose",
    "session_csrf",
    "product_details",
    "csp",
    "mozilla_django_oidc",
    "cities_light",
    "axes",
    "mozillians",
    "mozillians.users",
    "mozillians.phonebook",
    "mozillians.groups",
    "mozillians.common",
    "mozillians.api",
    "mozillians.mozspaces",
    "mozillians.funfacts",
    "mozillians.announcements",
    "mozillians.humans",
    "mozillians.geo",
    "sorl.thumbnail",
    "raven.contrib.django.raven_compat",
)

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "mozillians.common.middleware.LocaleURLMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "mozillians.common.middleware.HSTSPreloadMiddleware",  # Must be before security middleware
    "mozillians.common.middleware.ReferrerPolicyMiddleware",  # Must be before security middleware
    "django.middleware.security.SecurityMiddleware",
    "session_csrf.CsrfMiddleware",  # Must be after auth middleware.
    # 'mozilla_django_oidc.middleware.SessionRefresh',
    "django.contrib.messages.middleware.MessageMiddleware",
    "csp.middleware.CSPMiddleware",
    "mozillians.phonebook.middleware.UsernameRedirectionMiddleware",
    "axes.middleware.AxesMiddleware",
]

#############################
# Database configuration
#############################

DATABASES = {"default": config("DATABASE_URL", cast=db_url)}

############################
# Environment variables
############################
DEV = config("DEV", default=False, cast=bool)
DEBUG = config("DEBUG", default=False, cast=bool)

ADMIN_ALIAS = config("ADMIN_ALIAS", default="mozillians-admins@mozilla.com")
ADMINS = (("Mozillians.org Admins", ADMIN_ALIAS),)
MANAGERS = ADMINS
DOMAIN = config("DOMAIN", default="mozillians.org")
PROTOCOL = config("PROTOCOL", default="https://")
PORT = config("PORT", default=443, cast=int)
SITE_URL = config("SITE_URL", default="https://mozillians.org")
SECRET_KEY = config("SECRET_KEY", default="")

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1", cast=Csv())

# Site ID is used by Django's Sites framework.
SITE_ID = 1

X_FRAME_OPTIONS = config("X_FRAME_OPTIONS", default="DENY")

# Sessions
SESSION_COOKIE_HTTPONLY = config("SESSION_COOKIE_HTTPONLY", default=True, cast=bool)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
SESSION_COOKIE_NAME = config("SESSION_COOKIE_NAME", default="mozillians_sessionid")
ANON_ALWAYS = config("ANON_ALWAYS", default=True, cast=bool)

# Security middleware
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool
)
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
ENABLE_HSTS_PRELOAD = config("ENABLE_HSTS_PRELOAD", default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = config(
    "SECURE_CONTENT_TYPE_NOSNIFF", default=True, cast=bool
)
SECURE_BROWSER_XSS_FILTER = config("SECURE_BROWSER_XSS_FILTER", default=True, cast=bool)
ENABLE_REFERRER_HEADER = config("ENABLE_REFERRER_HEADER", default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# L10n
TIME_ZONE = config("TIME_ZONE", default="America/Los_Angeles")
TEXT_DOMAIN = "django"
STANDALONE_DOMAINS = [TEXT_DOMAIN, "djangojs"]
LANGUAGE_CODE = config("LANGUAGE_CODE", default="en-US")
# Accepted locales
PROD_LANGUAGES = (
    "bn",
    "ca",
    "cs",
    "de",
    "en-CA",
    "en-US",
    "en-GB",
    "es",
    "hu",
    "fr",
    "it",
    "ko",
    "nl",
    "pl",
    "pt-BR",
    "pt-PT",
    "ro",
    "ru",
    "sk",
    "sl",
    "sq",
    "sr",
    "sv-SE",
    "te",
    "zh-TW",
    "zh-CN",
    "lt",
    "ja",
    "hsb",
    "dsb",
    "uk",
    "kab",
    "fy-NL",
)
DEV_LANGUAGES = PROD_LANGUAGES

EXEMPT_L10N_URLS = [
    "^/oidc/authenticate/",
    "^/oidc/callback/",
    "^/verify/identity/",
    "^/verify/identity/callback/",
    "^/api/v1/",
    "^/api/v2/",
    "^/api/v3/",
    "^/admin/",
    "^/beta/.*",
]


def get_langs():
    return DEV_LANGUAGES if DEV else PROD_LANGUAGES


LANGUAGE_URL_MAP = dict([(i.lower(), i) for i in get_langs()])


def lazy_langs():
    from product_details import product_details

    return [
        (lang.lower(), product_details.languages[lang]["native"])
        for lang in get_langs()
        if lang in product_details.languages
    ]


# Workaround after performance issue
LANGUAGES = lazy_langs()

# Not all URLs need locale.
SUPPORTED_NONLOCALES = [
    "media",
    "static",
    "admin",
    "csp",
    "api",
    "contribute.json",
    "admin",
    "autocomplete",
    "humans.txt",
]

# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": config("CACHE_URL", default="127.0.0.1:11211"),
    }
}

# Google Analytics
GA_ACCOUNT_CODE = config("GA_ACCOUNT_CODE", default="UA-35433268-19")

# Sorl settings
THUMBNAIL_DUMMY = config("THUMBNAIL_DUMMY", default=True, cast=bool)
THUMBNAIL_PREFIX = config("THUMBNAIL_PREFIX", default="uploads/sorl-cache/")

# Avatar
USER_AVATAR_DIR = config("USER_AVATAR_DIR", default="uploads/userprofile")
# Set default avatar for user profiles
DEFAULT_AVATAR = config("DEFAULT_AVATAR", default="img/default_avatar.png")
DEFAULT_AVATAR_URL = config(
    "DEFAULT_AVATAR_URL", default=urljoin(MEDIA_URL, DEFAULT_AVATAR)
)
DEFAULT_AVATAR_PATH = os.path.join(MEDIA_ROOT, DEFAULT_AVATAR)

# Mozspace
MOZSPACE_PHOTO_DIR = config("MOZSPACE_PHOTO_DIR", default="uploads/mozspaces")

# Announcements
ANNOUNCEMENTS_PHOTO_DIR = config(
    "ANNOUNCEMENTS_PHOTO_DIR", default="uploads/announcements"
)

MESSAGE_STORAGE = config(
    "MESSAGE_STORAGE", default="django.contrib.messages.storage.session.SessionStorage"
)

# timezone
USE_TZ = config("USE_TZ", default=True, cast=bool)

# Pagination: Items per page.
ITEMS_PER_PAGE = config("ITEMS_PER_PAGE", default=24, cast=int)

# Django compressor
COMPRESS_OFFLINE = config("COMPRESS_OFFLINE", default=True, cast=bool)
COMPRESS_ENABLED = config("COMPRESS_ENABLED", default=True, cast=bool)
# Use custom CSS, JS compressors to enable SRI support
COMPRESS_CSS_COMPRESSOR = "mozillians.common.compress.SRICssCompressor"
COMPRESS_JS_COMPRESSOR = "mozillians.common.compress.SRIJsCompressor"

# humans.txt
HUMANSTXT_GITHUB_REPO = config(
    "HUMANSTXT_GITHUB_REPO",
    default="https://api.github.com/repos/mozilla/mozillians/contributors",
)
HUMANSTXT_LOCALE_REPO = config(
    "HUMANSTXT_LOCALE_REPO",
    default="https://api.github.com/repos/mozilla-l10n/mozillians-l10n/contributors",
)
HUMANSTXT_FILE = os.path.join(STATIC_ROOT, "humans.txt")
HUMANSTXT_URL = urljoin(STATIC_URL, "humans.txt")

# Vouching
# All accounts limited in 6 vouches total. Bug 997400.
VOUCH_COUNT_LIMIT = config("VOUCH_COUNT_LIMIT", default=6, cast=int)
# All accounts need 1 vouches to be able to vouch.
CAN_VOUCH_THRESHOLD = config("CAN_VOUCH_THRESHOLD", default=3, cast=int)
AUTO_VOUCH_DOMAINS = (
    "mozilla.com",
    "mozilla.org",
    "mozillafoundation.org",
    "getpocket.com",
)
AUTO_VOUCH_REASON = "An automatic vouch for being a Mozilla employee."

USERNAME_MAX_LENGTH = config("USERNAME_MAX_LENGTH", default=30, cast=int)

# On Login, we redirect through register.
LOGIN_URL = config("LOGIN_URL", default="/")
LOGIN_REDIRECT_URL = config("LOGIN_REDIRECT_URL", default="/")

# django-mobility
MOBILE_COOKIE = config("MOBILE_COOKIE", default="mobile")


OIDC_STORE_ACCESS_TOKEN = config("OIDC_STORE_ACCESS_TOKEN", default=True, cast=bool)
OIDC_RP_CLIENT_ID = config("OIDC_RP_CLIENT_ID", default="")
OIDC_RP_CLIENT_SECRET = config("OIDC_RP_CLIENT_SECRET", default="")
OIDC_RP_CLIENT_SECRET_ENCODED = config(
    "OIDC_RP_CLIENT_SECRET_ENCODED", default=True, cast=bool
)
OIDC_OP_DOMAIN = config("OIDC_OP_DOMAIN", default="auth.mozilla.auth0.com")
OIDC_OP_AUTHORIZATION_ENDPOINT = config("OIDC_OP_AUTHORIZATION_ENDPOINT", default="")
OIDC_OP_TOKEN_ENDPOINT = config("OIDC_OP_TOKEN_ENDPOINT", default="")
OIDC_OP_USER_ENDPOINT = config("OIDC_OP_USER_ENDPOINT", default="")
OIDC_RP_VERIFICATION_CLIENT_ID = config("OIDC_RP_VERIFICATION_CLIENT_ID", default="")
OIDC_RP_VERIFICATION_CLIENT_SECRET = config(
    "OIDC_RP_VERIFICATION_CLIENT_SECRET", default=""
)
OIDC_PROMPT = "select_account"
OIDC_ACCOUNT_LINKING = "true"
OIDC_CREATE_USER = False
OIDC_EXEMPT_URLS = [
    "/verify/identity/",
    "/verify/identity/callback/",
]
OIDC_RP_SCOPES = "openid email profile"

# AWS credentials
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")

# Setup django-axes
AXES_PROXY_COUNT = 1
IPWARE_META_PRECEDENCE_ORDER = (
    "HTTP_X_FORWARDED_FOR",
    "IPWARE_META_PRECEDENCE_ORDER",
    "REMOTE_ADDR",
)
AXES_FAILURE_LIMIT = config("AXES_FAILURE_LIMIT", default=10, cast=int)
# block for one hour
AXES_COOLOFF_TIME = config("AXES_COOLOFF_TIME", default=1, cast=int)
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = config(
    "AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP", default=True, cast=bool
)

# Setup logging and sentry
RAVEN_CONFIG = config("RAVEN_CONFIG", cast=json.loads, default="{}")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "root": {
        "level": "INFO",
        "handlers": ["sentry"],
    },
    "formatters": {
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[%(server_time)s] %(message)s",
        },
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
    },
    "handlers": {
        "sentry": {
            "level": "WARNING",
            "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.server": {
            "level": "INFO",
            "handlers": ["django.server"],
            "propagate": False,
        },
        "django.db.backends": {
            "level": "WARNING",
            "handlers": ["console", "sentry"],
            "propagate": False,
        },
        "sentry.errors": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        },
        "raven": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

#######################
# Project Configuration
#######################
# Templates.
# List of callables that know how to import templates from various sources.
COMMON_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.template.context_processors.debug",
    "django.template.context_processors.media",
    "django.template.context_processors.request",
    "django.template.context_processors.static",
    "django.template.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "session_csrf.context_processor",
    "mozillians.common.context_processors.i18n",
    "mozillians.common.context_processors.globals",
    "mozillians.common.context_processors.current_year",
    "mozillians.common.context_processors.canonical_path",
]

TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "DIRS": [Path("mozillians/jinja2").resolve()],
        "NAME": "jinja2",
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": DEBUG,
            "app_dirname": "jinja2",
            "match_extension": None,
            "newstyle_gettext": True,
            "undefined": "jinja2.Undefined",
            "extensions": DEFAULT_EXTENSIONS
            + ["compressor.contrib.jinja2ext.CompressorExtension"],
            "context_processors": COMMON_CONTEXT_PROCESSORS,
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [Path("mozillians/templates").resolve()],
        "APP_DIRS": True,
        "OPTIONS": {"debug": DEBUG, "context_processors": COMMON_CONTEXT_PROCESSORS},
    },
]


def COMPRESS_JINJA2_GET_ENVIRONMENT():
    from django.template import engines

    return engines["jinja2"].env


# Storage of static files
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_CSS_FILTERS = (
    "compressor.filters.css_default.CssAbsoluteFilter",
    "compressor.filters.cssmin.CSSMinFilter",
)
COMPRESS_PRECOMPILERS = (("text/less", 'lessc "{infile}" "{outfile}"'),)

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
)

# Authentication settings
AUTHENTICATION_BACKENDS = (
    "axes.backends.AxesBackend",
    "django.contrib.auth.backends.ModelBackend",
    "mozillians.common.authbackend.MozilliansAuthBackend",
)

# Auth
PWD_ALGORITHM = config("PWD_ALGORITHM", default="bcrypt")

HMAC_KEYS = {
    "2011-01-01": "cheesecake",
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.BCryptPasswordHasher",
]

MAX_PHOTO_UPLOAD_SIZE = 8 * (1024 ** 2)

# Django-CSP
CSP_REPORT_ONLY = config("CSP_REPORT_ONLY", default=False, cast=bool)
CSP_REPORT_ENABLE = config("CSP_REPORT_ENABLE", default=True, cast=bool)
CSP_DEFAULT_SRC = (
    "'self'",
    "https://cdn.mozillians.org",
)

CSP_FONT_SRC = (
    "'self'",
    "https://*.mozilla.net",
    "https://*.mozilla.org",
    "https://cdn.mozillians.org",
    "https://cdn-staging.mozillians.org",
    "https://fonts.gstatic.com",
)

CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https://*.mozilla.net",
    "https://*.mozilla.org",
    "*.google-analytics.com",
    "*.gravatar.com",
    "*.wp.com",
    "https://*.mozillians.org",
)

CSP_SCRIPT_SRC = (
    "'self'",
    "https://cdn.mozillians.org",
    "https://cdn-staging.mozillians.org",
    "https://www.mozilla.org",
    "https://*.mozilla.net",
    "https://*.google-analytics.com",
    "https://www.google.com/recaptcha/",
    "https://www.gstatic.com/recaptcha/",
    "https://www.googletagmanager.com",
    # Allow Django's admin scripts
    "'sha256-UtImx13kPrbu3A8Xh9LfC9WbLVFznPB3z3KlhHI+WsM='",
    "'sha256-YAeNgc46QF0YbTBOhlJJtwaOwJTu1UEvFVe3ljLBobg='",
    "'sha256-SnCGK9WisvmkewWrjN4QT2Xmx3i1GHWA56tgHFJjL0w='",
    "'sha256-fH3rM69L3MlQuLHwmENXZ9SSP9u+7mECRGOpE5pY/Hw='",
    "'sha256-lV6Q4R6n6P5zkatU4DiQ40kagqmlwvF0XXvRV/UfpPU='",
)

CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.mozillians.org",
    "https://cdn-staging.mozillians.org",
    "https://www.mozilla.org",
    "https://*.mozilla.net",
    "https://fonts.googleapis.com",
)

CSP_FRAME_SRC = (
    "'self'",
    "https://www.google.com/recaptcha/",
)

STRONGHOLD_EXCEPTIONS = [
    "^%s" % MEDIA_URL,  # noqa
    "^/csp/",
    "^/admin/",
    "^/api/",
    "^/oidc/authenticate/",
    "^/oidc/callback/",
    # Allow autocomplete urls for profile registration
    "^/[\w-]+/skills-autocomplete/",
    "^/[\w-]+/country-autocomplete/",
    "^/[\w-]+/city-autocomplete/",
    "^/[\w-]+/region-autocomplete/",
    "^/[\w-]+/timezone-autocomplete/",
]

if DEV:
    CSP_FONT_SRC += (
        "http://*.mozilla.net",
        "http://*.mozilla.org",
    )

    CSP_IMG_SRC += (
        "http://*.mozilla.net",
        "http://*.mozilla.org",
        "http://dinopark.mozilla.community",
    )
    CSP_SCRIPT_SRC += (
        "'unsafe-inline'",
        "'unsafe-eval'",
        "http://*.mozilla.net",
        "http://*.mozilla.org",
        "http://cdn.jsdelivr.net",
        "http://dinopark.mozilla.community",
    )
    CSP_STYLE_SRC += (
        "http://*.mozilla.net",
        "http://*.mozilla.org",
        "http://cdn.jsdelivr.net",
        "http://dinopark.mozilla.community",
    )

if DEBUG:
    for backend in TEMPLATES:
        backend["OPTIONS"]["debug"] = DEBUG
