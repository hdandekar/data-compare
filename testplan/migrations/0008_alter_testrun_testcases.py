# Generated by Django 5.0.1 on 2024-03-28 06:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("testplan", "0007_testcasestatus_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="testrun",
            name="testcases",
            field=models.ManyToManyField(blank=True, through="testplan.TestRunCases", to="testplan.testcase"),
        ),
    ]
