import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from testplan.models import Module, Project


@login_required
def project_index(request):
    return render(request, "project_index.html")


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    fields = ["name", "project_code", "description", "members", "owner"]
    template_name = "project_form.html"

    def form_valid(self, form):
        project = form.save(commit=False)
        project.created_by = self.request.user
        project.save()
        form.save_m2m()
        project.members.add(self.request.user.id)
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "listChanged": None,
                        "showMessage": f"{project.name} added.",
                        "eventType": "created",
                    }
                )
            },
        )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    fields = ["name", "project_code", "description", "members", "owner"]
    template_name = "project_form.html"

    def form_valid(self, form):
        project = form.save(commit=False)
        project.modified_by = self.request.user
        project.save()
        form.save_m2m()
        project.members.add(self.request.user.id)
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "listChanged": None,
                        "showMessage": f"{project.name} updated.",
                        "eventType": "updated",
                    }
                )
            },
        )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_message(self, cleaned_data):
        name = cleaned_data["name"]
        return self.success_message % dict(
            {
                "cleaned_data": cleaned_data,
                "name": name,
                "object_id": self.kwargs["project_id"],
            }
        )

    def get_success_url(self):
        return redirect("projects")

    def test_func(self):
        if self.request.user == self.get_object().owner:
            return True
        return False

    def handle_no_permission(self):
        project = self.get_object()
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "showMessage": f"You do not have permission to edit '{project.name}'",
                        "eventType": "permissiondenied",
                    }
                )
            },
        )


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "project_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["access_records"] = (
            Project.objects.filter(members__id__exact=self.request.user.id).order_by("-owner").select_related("owner")
        )  # noqa: E501
        return context


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    template_name = "project_confirm_delete.html"

    def get_object(self, queryset=None):
        project = Project.objects.get(id=self.kwargs.get("pk"))
        return project

    def post(self, *args, **kwargs):
        project = self.get_object()
        try:
            self.get_object().delete()
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "listChanged": None,
                            "showMessage": f"{project.name} deleted.",
                            "eventType": "deleted",
                        }
                    )
                },
            )
        except ProtectedError as e:
            print("Error is: ", e)
            print("Exception Type is:", e.__class__.__name__)
            print("Exception message is: ", repr(e))
            print("Type of arg[1]", type(e.args[1]))
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "listChanged": None,
                            "showMessage": "'{}' cannot be deleted as it has {} dependent modules".format(
                                project.name, len(e.args[1])
                            ),
                            "eventType": "deleted",
                        }
                    )
                },
            )

    def test_func(self):
        project = self.get_object()
        if project.owner == self.request.user:
            return True
        return False

    def handle_no_permission(self):
        project = self.get_object()
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "showMessage": f"You do not have permission to delete '{project.name}'",
                        "eventType": "permissiondenied",
                    }
                )
            },
        )


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "project_detail.html"


class ModuleCreateView(LoginRequiredMixin, CreateView):
    model = Module
    fields = [
        "name",
    ]
    template_name = "module_form.html"

    def form_valid(self, form):
        module = form.save(commit=False)
        module.created_by = self.request.user
        module.modified_by = self.request.user
        module.project = Project.objects.get(id=self.kwargs["project_id"])
        module.save()
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "listChanged": None,
                        "showMessage": f"{module.name} added.",
                        "eventType": "created",
                    }
                )
            },
        )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ModuleListView(LoginRequiredMixin, ListView):
    model = Module
    template_name = "module_list.html"

    def get_queryset(self):
        project = get_object_or_404(Project, id=self.kwargs["project_id"])
        return Module.objects.filter(project=project).order_by("-created_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(id=self.kwargs["project_id"])
        return context


class ModuleUpdateView(LoginRequiredMixin, UpdateView):
    model = Module
    fields = [
        "name",
    ]
    template_name = "module_form.html"

    def form_valid(self, form):
        module = form.save(commit=False)
        module.modified_by = self.request.user
        module.save()
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "listChanged": None,
                        "showMessage": f"'{module.name}' module updated.",
                        "eventType": "updated",
                    }
                )
            },
        )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_message(self, cleaned_data):
        name = cleaned_data["name"]
        return self.success_message % dict(
            {
                "cleaned_data": cleaned_data,
                "name": name,
                "object_id": self.kwargs["module_id"],
            }
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        project_id = self.kwargs.get("project_id")
        module_id = self.kwargs.get("module_id")
        queryset = queryset.filter(project=project_id, id=module_id)
        obj = queryset.get()
        return obj


class ModuleDeleteView(LoginRequiredMixin, DeleteView):
    model = Module
    template_name = "project_confirm_delete.html"

    def get_object(self, queryset=None):
        project = Module.objects.get(id=self.kwargs.get("module_id"))
        return project

    def post(self, *args, **kwargs):
        project = self.get_object()
        try:
            self.get_object().delete()
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "listChanged": None,
                            "showMessage": f"{project.name} deleted.",
                            "eventType": "deleted",
                        }
                    )
                },
            )
        except ProtectedError as e:
            print("Error is: ", e)
            print("Exception Type is:", e.__class__.__name__)
            print("Exception message is: ", repr(e))
            print("Type of arg[1]", type(e.args[1]))
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "listChanged": None,
                            "showMessage": "Cannot delete '{}' as there are {} modules".format(
                                project.name, len(e.args[1])
                            ),
                            "eventType": "deleted",
                        }
                    )
                },
            )


@login_required
def module_delete(request, project_id, module_id):
    module = Module.objects.get(id=module_id)

    if request.method == "POST":
        module.delete()
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "listChanged": None,
                        "showMessage": f"{module.name} deleted successfully",
                        "eventType": "deleted",
                    }
                )
            },
        )

    return render(request, "module_delete_confirm.html", {"module": module})
