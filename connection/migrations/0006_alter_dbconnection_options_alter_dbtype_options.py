# Generated by Django 5.0.1 on 2024-02-29 03:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("connection", "0005_dbtype_dbconnection_create_dt_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="dbconnection",
            options={"verbose_name": "DB Connection"},
        ),
        migrations.AlterModelOptions(
            name="dbtype",
            options={"verbose_name": "DB Type"},
        ),
    ]