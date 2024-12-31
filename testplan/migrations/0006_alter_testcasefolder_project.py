# Generated by Django 5.1.4 on 2024-12-31 04:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0009_alter_dbconnection_dbname_and_more"),
        ("testplan", "0005_alter_testcase_folder"),
    ]

    operations = [
        migrations.AlterField(
            model_name="testcasefolder",
            name="project",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="project_folders",
                to="project.project",
            ),
        ),
    ]