# Generated by Django 5.0.1 on 2024-03-01 09:23

import testplan.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("testplan", "0005_rename_sourcedbid_testcase_sourcedb_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="module",
            name="modified_by",
            field=models.ForeignKey(
                null=True,
                on_delete=models.SET(testplan.models.get_deleted_user_instance),
                related_name="module_modified_by",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
