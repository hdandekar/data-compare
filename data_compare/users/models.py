import os

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db.models import (CharField, EmailField, ImageField, TextField,
                              URLField)
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from data_compare.users.managers import UserManager


class User(AbstractUser):
    def user_profile_avatar_path(self, instance):
        ext = instance.split(".")[-1]
        return f"{self.id}/avatars/profile.{ext}"

    """
    Default custom user model for data-compare.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore
    designation = CharField(max_length=255, blank=True)
    about_me = TextField(blank=True, null=True)
    avatar = ImageField(upload_to=user_profile_avatar_path, blank=True)
    website = URLField(blank=True)
    github_link = CharField(blank=True, max_length=50)
    twitter_link = CharField(blank=True, max_length=50)
    phoneNumberRegex = RegexValidator(regex=r"^\+?1?\d{8,15}$")
    mobile_number = CharField(validators=[phoneNumberRegex], max_length=16, blank=True)
    address = CharField(blank=True, max_length=255)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:user_detail", kwargs={"pk": self.id})

    def filename(self):
        return os.path.basename(self.avatar.name)
