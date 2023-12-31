# Generated by Django 3.1.1 on 2020-09-28 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('connection', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='connection',
            name='schema_name',
            field=models.CharField(default="NA", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='connection',
            name='warehouse_name',
            field=models.CharField(default="NA", max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='connection',
            name='dbtype',
            field=models.CharField(choices=[('MySQL', 'MySQL'), ('Snowflake', 'Snowflake'), ('MSSQL', 'MS SQL Server')], max_length=50),
        ),
    ]
