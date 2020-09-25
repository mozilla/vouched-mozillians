from functools import update_wrapper

from django.conf import settings
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse
from django.db.models import Count, Q

from mozillians.common.templatetags.helpers import get_datetime
from mozillians.users.admin_forms import UserProfileAdminForm
from mozillians.users.models import (PUBLIC, IdpProfile,
                                     UsernameBlacklist, UserProfile, Vouch)

admin.site.unregister(Group)


Q_PUBLIC_PROFILES = Q()
for field in UserProfile.privacy_fields():
    key = 'privacy_%s' % field
    Q_PUBLIC_PROFILES |= Q(**{key: PUBLIC})


def update_vouch_flags_action():
    """Update can_vouch, is_vouched flag action."""

    def update_vouch_flags(modeladmin, request, queryset):
        for profile in queryset:
            vouches_received = profile.vouches_received.count()
            profile.can_vouch = vouches_received >= settings.CAN_VOUCH_THRESHOLD
            profile.is_vouched = vouches_received > 0
            profile.save()
    update_vouch_flags.short_description = 'Update vouch flags'
    return update_vouch_flags


class SuperUserFilter(SimpleListFilter):
    """Admin filter for superusers."""
    title = 'has access to admin interface'
    parameter_name = 'superuser'

    def lookups(self, request, model_admin):
        return (('False', 'No'),
                ('True', 'Yes'))

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        value = self.value() == 'True'
        return queryset.filter(user__is_staff=value)


class PublicProfileFilter(SimpleListFilter):
    """Admin filter for public profiles."""
    title = 'public profile'
    parameter_name = 'public_profile'

    def lookups(self, request, model_admin):
        return (('False', 'No'),
                ('True', 'Yes'))

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        if self.value() == 'True':
            return queryset.filter(Q_PUBLIC_PROFILES)

        return queryset.exclude(Q_PUBLIC_PROFILES)


class DateJoinedFilter(SimpleListFilter):
    """Admin filter for date joined."""
    title = 'date joined'
    parameter_name = 'date_joined'

    def lookups(self, request, model_admin):
        join_dates = User.objects.values_list('date_joined', flat=True)
        join_years = [x.year for x in join_dates]
        return [(str(x), x) for x in set(join_years)]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(user__date_joined__year=self.value())
        return queryset


class LastLoginFilter(SimpleListFilter):
    """Admin filter for last login."""
    title = 'last login'
    parameter_name = 'last_login'

    def lookups(self, request, model_admin):
        # Number is in days
        return (('<7', 'Less than a week'),
                ('<30', 'Less than a month'),
                ('<90', 'Less than 3 months'),
                ('<180', 'Less than 6 months'),
                ('>180', 'Between 6 and 12 months'),
                ('>360', 'More than a year'))

    def queryset(self, request, queryset):

        if self.value() == '<7':
            return queryset.filter(user__last_login__gte=get_datetime(-7))
        elif self.value() == '<30':
            return queryset.filter(user__last_login__gte=get_datetime(-30))
        elif self.value() == '<90':
            return queryset.filter(user__last_login__gte=get_datetime(-90))
        elif self.value() == '<180':
            return queryset.filter(user__last_login__gte=get_datetime(-180))
        elif self.value() == '>180':
            return queryset.filter(user__last_login__lt=get_datetime(-180),
                                   user__last_login__gt=get_datetime(-360))
        elif self.value() == '>360':
            return queryset.filter(user__last_login__lt=get_datetime(-360))
        return queryset


class UsernameBlacklistAdmin(admin.ModelAdmin):
    """UsernameBlacklist Admin."""
    save_on_top = True
    search_fields = ['value']
    list_filter = ['is_regex']
    list_display = ['value', 'is_regex']


admin.site.register(UsernameBlacklist, UsernameBlacklistAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ['full_name', 'user__email', 'user__username', 'is_staff']
    readonly_fields = ['date_vouched', 'vouched_by', 'user', 'date_joined', 'last_login',
                       'is_vouched', 'can_vouch']
    form = UserProfileAdminForm
    list_filter = ['is_vouched', 'can_vouch', DateJoinedFilter,
                   LastLoginFilter, SuperUserFilter, PublicProfileFilter,
                   'externalaccount__type']
    save_on_top = True
    list_display = ['full_name', 'email', 'username', 'is_vouched', 'can_vouch',
                    'number_of_vouchees', 'date_joined']
    list_display_links = ['full_name', 'email', 'username']
    actions = [update_vouch_flags_action()]

    fieldsets = (
        ('Account', {
            'fields': ('full_name', 'username', 'email',
                       'auth0_user_id', 'is_staff',)
        }),
        (None, {
            'fields': ('date_mozillian',)
        }),
        ('Important dates', {
            'fields': ('date_joined', 'last_login')
        }),
        ('Vouch Info', {
            'fields': ('date_vouched', 'is_vouched', 'can_vouch')
        }),
        ('Privacy Settings', {
            'fields': ('privacy_full_name', 'privacy_email', 'privacy_data_mozillians',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super(UserProfileAdmin, self).get_queryset(request)
        qs = qs.annotate(vouches_made_count=Count('vouches_made'))
        return qs

    def get_actions(self, request):
        """Return bulk actions for UserAdmin without bulk delete."""
        actions = super(UserProfileAdmin, self).get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def get_urls(self):
        """Return custom and UserProfileAdmin urls."""

        def wrap(view):

            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        urls = super(UserProfileAdmin, self).get_urls()
        return urls

    def email(self, obj):
        return obj.user.email
    email.admin_order_field = 'user__email'

    def username(self, obj):
        return obj.user.username
    username.admin_order_field = 'user__username'

    def is_vouched(self, obj):
        return obj.userprofile.is_vouched
    is_vouched.boolean = True
    is_vouched.admin_order_field = 'is_vouched'

    def vouched_by(self, obj):
        voucher = obj.vouched_by
        if voucher:
            voucher_url = reverse('admin:auth_user_change', args=[voucher.id])
            return '<a href="%s">%s</a>' % (voucher_url, voucher)
    vouched_by.admin_order_field = 'vouched_by'
    vouched_by.allow_tags = True

    def number_of_vouchees(self, obj):
        """Return the number of vouchees for obj."""
        return obj.vouches_made_count
    number_of_vouchees.admin_order_field = 'vouches_made_count'

    def last_login(self, obj):
        return obj.user.last_login

    def date_joined(self, obj):
        return obj.user.date_joined


admin.site.register(UserProfile, UserProfileAdmin)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class GroupAdmin(GroupAdmin):
    pass


admin.site.register(Group, GroupAdmin)


class VouchAdmin(admin.ModelAdmin):
    save_on_top = True
    search_fields = ['voucher__user__username', 'voucher__full_name',
                     'vouchee__user__username', 'vouchee__full_name',
                     'voucher__user__email', 'vouchee__user__email', 'description']
    list_display = ['vouchee', 'voucher', 'date', 'autovouch']
    list_filter = ['autovouch']


admin.site.register(Vouch, VouchAdmin)


class IdpProfileAdmin(admin.ModelAdmin):
    resource_class = IdpProfile
    list_display = ['type', 'profile', 'auth0_user_id', 'email', 'primary']
    list_filter = ['type']
    search_fields = ['profile__user__email', 'profile__full_name',
                     'profile__user__username', 'email', 'auth0_user_id']

    class Meta:
        model = IdpProfile


admin.site.register(IdpProfile, IdpProfileAdmin)
