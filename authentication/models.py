
from django.db import models


class UserAuthentication(models.Model):
    """
    User Authentication information using OAuth2.0 sign-ins.

    Attributes
    ----------
    auth_id : str
        The user's auth id that is returned from the oAuth service being used for PresQT logins.
    auth_token : str
        The oAuth service authentication token. PresQT will use this to tie a user to an 
        authentication instance.
    refresh_token : str
        The oAuth service authentication refresh token. Used to get a user a new auth_token.
    """
    auth_id = models.CharField(primary_key=True, editable=False, max_length=100)
    auth_token = models.CharField(null=True, blank=True, max_length=100)
    refresh_token = models.CharField(null=True, blank=True, max_length=100)
    curate_nd_token = models.CharField(null=True, blank=True, max_length=100)
    figshare_token = models.CharField(null=True, blank=True, max_length=100)
    github_token = models.CharField(null=True, blank=True, max_length=100)
    gitlab_token = models.CharField(null=True, blank=True, max_length=100)
    osf_token = models.CharField(null=True, blank=True, max_length=100)
    zenodo_token = models.CharField(null=True, blank=True, max_length=100)

    class Meta:
        db_table = "user_authentication"
        verbose_name_plural = "UserAuthentication"

    def __str__(self):
        return self.auth_id
