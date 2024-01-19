from django.contrib import admin

from .models import DbConnection


@admin.register(DbConnection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "hostname", "dbtype", "username", "password", "portno"]
