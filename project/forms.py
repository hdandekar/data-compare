from django import forms

from .models import DbConnection


class ConnectionForm(forms.ModelForm):
    class Meta:
        model = DbConnection
        fields = [
            "dbtype",
            "name",
            "dbname",
            "hostname",
            "username",
            "password",
            "portno",
            "schema_name",
        ]
