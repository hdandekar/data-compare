from django.contrib import admin
from .models import TestCase


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['sourcedbid', 'sourcesql',
                    'targetdbid', 'targetsql', 'keycolumns']
    # list_display = ['id', 'name', 'hostname',
    #                 'dbtype', 'username', 'password', 'portno']
