from django import forms

from testplan.models import TestCase, TestRun


class TestRunForm(forms.ModelForm):
    class Meta:
        model = TestRun
        fields = ("testcases", "project", "name")

    def __init__(self, *args, **kwargs):
        proj_id = kwargs["project"]
        self.request = kwargs.pop("project")
        super().__init__(*args, **kwargs)
        self.fields["testcases"].widget = forms.CheckboxSelectMultiple()
        self.fields["testcases"].queryset = TestCase.objects.filter(project=proj_id)
