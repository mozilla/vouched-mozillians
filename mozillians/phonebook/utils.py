from mozillians.users.models import IdpProfile


def get_profile_link_by_email(email):
    try:
        idp_profile = IdpProfile.objects.get(email=email, primary=True)
    except (IdpProfile.DoesNotExist, IdpProfile.MultipleObjectsReturned):
        return ""
    else:
        return idp_profile.profile.get_absolute_url()
