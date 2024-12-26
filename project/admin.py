from django.contrib import admin

from .models import DbConnection, DbType


@admin.register(DbConnection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "hostname", "dbtype", "username", "password", "portno", "created_dt"]


@admin.register(DbType)
class DbTypeAdmin(admin.ModelAdmin):
    list_display = ["dbname"]
