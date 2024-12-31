# Generated by Django 5.1.4 on 2024-12-30 10:37

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import testplan.models


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0009_alter_dbconnection_dbname_and_more"),
        ("testplan", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="testruntestcasehistory",
            options={"ordering": ["-id"]},
        ),
        migrations.CreateModel(
            name="TestCaseFolder",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("updated_date", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=255)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=models.SET(testplan.models.get_deleted_user_instance),
                        related_name="tc_folder_created_by",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "modified_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=models.SET(testplan.models.get_deleted_user_instance),
                        related_name="tc_folder_modified_by",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subfolder",
                        to="testplan.testcasefolder",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="project.project",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="testcase",
            name="folder",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="folder_testcases",
                to="testplan.testcasefolder",
            ),
        ),
    ]