from django.contrib import admin

from .models import DbConnection, DbType, Project


@admin.register(DbConnection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "hostname",
        "dbtype",
        "username",
        "password",
        "portno",
        "created_dt",
    ]


@admin.register(DbType)
class DbTypeAdmin(admin.ModelAdmin):
    list_display = ["dbname"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "description",
        "project_slug",
        "project_code",
        "created_date",
        "updated_date",
        "owner",
        "members",
    ]

    def members(self, obj):
        return ", ".join([member.user.email for member in obj.projectmember_set.all()])
