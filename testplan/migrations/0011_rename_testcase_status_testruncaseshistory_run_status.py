# Generated by Django 5.0.1 on 2024-10-27 10:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("testplan", "0010_testruncaseshistory_comments"),
    ]

    operations = [
        migrations.RenameField(
            model_name="testruncaseshistory",
            old_name="testcase_status",
            new_name="run_status",
        ),
    ]
