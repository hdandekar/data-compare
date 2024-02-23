from django.contrib import admin

from .models import Module, Project


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
        "get_members",
    ]

    @admin.display(description="members")
    def get_members(self, obj):
        return [project.email for project in obj.members.all()]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ["project", "name", "created_date", "updated_date", "created_by", "modified_by"]
