from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from data_compare.users.models import User


def get_deleted_user_instance():
    return get_user_model().objects.get_or_create(username="deleted")[0]


class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    project_slug = models.SlugField(max_length=100, null=True, blank=True)
    project_code = models.CharField(max_length=6)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="project_created_by",
        on_delete=models.PROTECT,
    )
    members = models.ManyToManyField(User, related_name="projects", blank=True)

    class Meta:
        ordering = ["-updated_date"]

    def __str__(self):
        return self.name

    def get_absolute_url(self, kwargs):
        return reverse("project_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        slug_value = self.name
        self.project_slug = slugify(slug_value, allow_unicode=True)
        super().save(*args, **kwargs)


class Module(models.Model):
    project = models.ForeignKey(
        Project, related_name="modules", on_delete=models.PROTECT
    )
    name = models.CharField(max_length=255)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        related_name="module_created_by",
        on_delete=models.SET(get_deleted_user_instance),
    )
    modified_by = models.ForeignKey(
        User,
        related_name="module_modified_by",
        on_delete=models.SET(get_deleted_user_instance),
    )

    def __str__(self):
        return self.name
