from cities_light.models import Country
from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from mozillians.users import views as user_views

app_name = 'users'
urlpatterns = [
    # Admin urls for django-autocomplete-light.
    url('users-autocomplete/$', login_required(user_views.UsersAdminAutocomplete.as_view()),
        name='users-autocomplete'),
    url('vouchee-autocomplete/$', login_required(
        user_views.BaseProfileAdminAutocomplete.as_view()),
        name='vouchee-autocomplete'),
    url('voucher-autocomplete/$', login_required(user_views.VoucherAutocomplete.as_view()),
        name='voucher-autocomplete'),
    url('vouched-autocomplete/$', login_required(user_views.VouchedAutocomplete.as_view()),
        name='vouched-autocomplete'),
    url('staff-autocomplete/$', login_required(user_views.StaffProfilesAutocomplete.as_view()),
        name='staff-autocomplete'),
]
