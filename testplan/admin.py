from django.contrib import admin

from .models import TestCase, TestCaseStatus


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = [
        "tcname",
        "project",
        "sourcedb",
        "sourcesql",
        "targetdb",
        "targetsql",
        "keycolumns",
        "created_date",
        "updated_date",
        "created_by",
        "modified_by",
    ]


@admin.register(TestCaseStatus)
class TestCaseStatusAdmin(admin.ModelAdmin):
    list_display = ["status_value"]
