from django.forms import TextInput, Select
from django import forms
from .models import Connection
from django.contrib.auth.models import User


class ConnectionForm(forms.ModelForm):
    class Meta:
        model = Connection
        fields = ['dbtype', 'name', 'dbname', 'hostname',
                  'username', 'password', 'portno','warehouse_name','schema_name']
        labels = {
            'dbtype': 'Database Type',
            'name': 'Connection Name',
            'dbname': 'DB Name',
            'hostname': 'DB Host Name',
            'username': 'DB User Name',
            'password': 'DB Password',
            'portno': 'DB Port No#',
            'warehouse_name' : 'Snowflake Warehouse name',
            'schema_name': 'Snowflake Schema name'
        }
        widgets = {
            'dbtype': Select(attrs={'class': 'form-control'}),
            'name': TextInput(attrs={'class': 'form-control'}),
            'hostname': TextInput(attrs={'class': 'form-control'}),
            'dbname': TextInput(attrs={'class': 'form-control'}),
            'username': TextInput(attrs={'class': 'form-control'}),
            'password': TextInput(attrs={'class': 'form-control'}),
            'portno': TextInput(attrs={'class': 'form-control'}),
            'warehouse_name': TextInput(attrs={'class': 'form-control'}),
            'schema_name': TextInput(attrs={'class': 'form-control'}),
        }
