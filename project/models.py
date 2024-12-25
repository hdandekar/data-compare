from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from data_compare.users.models import User


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


class DbType(models.Model):
    dbname = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.dbname

    class Meta:
        verbose_name = "DB Type"


class DbConnection(models.Model):
    name = models.CharField(max_length=50)
    dbtype = models.ForeignKey(DbType, related_name="dbtype", on_delete=models.PROTECT, null=True)
    project = models.ForeignKey(Project, related_name="project", on_delete=models.CASCADE)
    dbname = models.CharField(max_length=200)
    hostname = models.CharField(max_length=200)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    portno = models.IntegerField()
    schema_name = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, related_name="connection", on_delete=models.PROTECT)
    create_dt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "DB Connection"
        ordering = ["-id"]
