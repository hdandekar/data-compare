from django import forms

from .models import Connection


class ConnectionForm(forms.ModelForm):
    class Meta:
        model = Connection
        fields = [
            "dbtype",
            "name",
            "dbname",
            "hostname",
            "username",
            "password",
            "portno",
            "warehouse_name",
            "schema_name",
        ]
