from django.db import models

# Create your models here.


class Connection(models.Model):
    DB_TYPES = (
        ("MySQL", "MySQL"),
        ("Snowflake", "Snowflake"),
        ("MSSQL", "MS SQL Server"),
    )
    name = models.CharField(max_length=50)
    dbtype = models.CharField(max_length=50, choices=DB_TYPES)
    dbname = models.CharField(max_length=200)
    hostname = models.CharField(max_length=200)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    portno = models.IntegerField()

    # Add new columns for Snowflake support
    warehouse_name = models.CharField(max_length=100)
    schema_name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
