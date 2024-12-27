from django.shortcuts import get_object_or_404, redirect

from project.models import Project


def user_is_admin(func):
    def wrap(request, *args, **kwargs):
        project_id = kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)
        if not project.projectmember_set.filter(
            user=request.user, role="admin"
        ).exists():
            return redirect("404_page")  # Or raise PermissionDenied if appropriate
        return func(request, *args, **kwargs)

    return wrap


def user_is_member(func):
    def wrap(request, *args, **kwargs):
        project_id = kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)
        if not project.projectmember_set.filter(
            user=request.user, role="member"
        ).exists():
            return redirect("404_page")  # Or raise PermissionDenied if appropriate
        return func(request, *args, **kwargs)

    return wrap
