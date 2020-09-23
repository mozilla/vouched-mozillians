from haystack import indexes
from mozillians.users.models import IdpProfile, UserProfile


class UserProfileIndex(indexes.SearchIndex, indexes.Indexable):
    """User Profile Search Index."""
    # Primary field of the index
    text = indexes.CharField(document=True, use_template=True)
    # profile information
    full_name = indexes.CharField(model_attr='full_name')
    privacy_full_name = indexes.IntegerField(model_attr='privacy_full_name')
    email = indexes.CharField(model_attr='email')
    privacy_email = indexes.IntegerField(model_attr='privacy_email')
    bio = indexes.CharField(model_attr='bio')
    privacy_bio = indexes.IntegerField(model_attr='privacy_bio')
    timezone = indexes.CharField(model_attr='timezone')
    privacy_timezone = indexes.IntegerField(model_attr='privacy_timezone')
    # location information - related fields
    country = indexes.CharField(model_attr='country__name', null=True)
    privacy_country = indexes.IntegerField(model_attr='privacy_country')
    region = indexes.CharField(model_attr='region__name', null=True)
    privacy_region = indexes.IntegerField(model_attr='privacy_region')
    city = indexes.CharField(model_attr='city__name', null=True)
    privacy_city = indexes.IntegerField(model_attr='privacy_city')

    # Django's username does not have privacy level
    username = indexes.CharField(model_attr='user__username')

    def get_model(self):
        return UserProfile

    def prepare_email(self, obj):
        # Do not index the email if it's already in the IdpProfiles
        if not obj.idp_profiles.exists():
            return obj.email
        return ''

    def index_queryset(self, using=None):
        """Exclude incomplete profiles from indexing."""
        return self.get_model().objects.complete()


class IdpProfileIndex(indexes.SearchIndex, indexes.Indexable):
    """IdpProfile Profile Search Index."""
    # Primary field of the index
    text = indexes.CharField(document=True, use_template=True)
    # IdpProfile information
    iemail = indexes.CharField(model_attr='email')
    privacy_iemail = indexes.IntegerField(model_attr='privacy')
    iusername = indexes.CharField(model_attr='username')
    privacy_iusername = indexes.IntegerField(model_attr='privacy')

    def get_model(self):
        return IdpProfile

    def index_queryset(self, using=None):
        """Only index unique emails."""
        all_idps = IdpProfile.objects.all()
        idps_ids = []
        unique_emails = set()

        for idp in all_idps:
            if idp.email not in unique_emails:
                idps_ids.append(idp.id)
                unique_emails.add(idp.email)
        return self.get_model().objects.filter(id__in=idps_ids)
