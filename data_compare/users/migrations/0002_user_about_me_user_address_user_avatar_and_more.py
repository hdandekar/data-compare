# Generated by Django 5.0 on 2024-01-26 04:06

import data_compare.users.models
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="about_me",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="address",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="avatar",
            field=models.ImageField(
                blank=True, null=True, upload_to=data_compare.users.models.User.user_profile_avatar_path
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="designation",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="user",
            name="github_link",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="mobile_number",
            field=models.CharField(
                blank=True,
                max_length=16,
                null=True,
                unique=True,
                validators=[django.core.validators.RegexValidator(regex="^\\+?1?\\d{8,15}$")],
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="twitter_link",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="website",
            field=models.URLField(blank=True, null=True),
        ),
    ]
