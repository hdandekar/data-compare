# Generated by Django 5.0.1 on 2024-03-28 02:41

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("connection", "0006_alter_dbconnection_options_alter_dbtype_options"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="dbtype",
            name="create_dt",
        ),
        migrations.AddField(
            model_name="dbtype",
            name="created_dt",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
