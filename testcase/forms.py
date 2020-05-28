from django import forms
from django.forms import Select, TextInput, Textarea
from testcase.models import TestCase


class TestCaseForm(forms.ModelForm):

    class Meta:
        model = TestCase
        fields = ('tcname', 'sourcedbid', 'sourcesql',
                  'targetdbid', 'targetsql', 'keycolumns')
        labels = {
            'tcname': 'Testcase Name',
            'sourcedbid': 'Source Connection',
            'sourcesql': 'Source SQL',
            'targetdbid': 'Target Connection',
            'targetsql': 'Target SQL',
            'keycolumns': 'Key Columns'
        }
        widgets = {
            # 'tcname': TextInput(attrs={'class': 'form-control'}),
            'sourcedbid': Select(attrs={'class': 'form-control'}),
            'sourcesql': Textarea(attrs={'class': 'form-control'}),
            'targetdbid': Select(attrs={'class': 'form-control'}),
            'targetsql': Textarea(attrs={'class': 'form-control'}),
            'keycolumns': TextInput(attrs={'class': 'form-control'}),
        }
