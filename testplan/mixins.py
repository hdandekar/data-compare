from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render

from .models import Project

_404_Page = "404.html"


class MemberPermissionMixin(UserPassesTestMixin):
    def test_func(self):
        try:
            project = Project.objects.get(id=self.kwargs["project_id"])
            if self.request.user in project.members.all():
                return True
            return False
        except ObjectDoesNotExist:
            return render(self.request, _404_Page)


class AdminPermissionMixin(UserPassesTestMixin):
    def test_func(self):
        try:
            project = Project.objects.get(id=self.kwargs["project_id"])
            if project.projectmember_set.filter(
                user=self.request.user, role="admin"
            ).exists():
                return True
            return False
        except ObjectDoesNotExist:
            return render(self.request, _404_Page)
