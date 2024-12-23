from django.db import models

from data_compare.users.models import User


class DbType(models.Model):
    dbname = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.dbname

    class Meta:
        verbose_name = "DB Type"


class DbConnection(models.Model):
    name = models.CharField(max_length=50)
    dbtype = models.ForeignKey(DbType, related_name="dbtype", on_delete=models.PROTECT, null=True)
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
