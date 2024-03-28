import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models.aggregates import Count
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from connection.models import DbConnection
from testplan.models import Module, Project, TestCase, TestRun, TestRunCases

_404_Page = "404.html"


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
        page_num = self.kwargs.get("page")
        member_projects = (
            Project.objects.filter(members__id__exact=self.request.user.id).order_by("-owner").select_related("owner")
        )
        paginator = Paginator(member_projects, per_page=20)
        context["projects"] = paginator.get_page(page_num)
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


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = "project_detail.html"

    def test_func(self):
        if self.request.user in self.get_object().members.all():
            return True
        return False

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


class ModuleCreateView(LoginRequiredMixin, CreateView):
    model = Module
    fields = [
        "name",
    ]
    template_name = "module_form.html"

    def form_valid(self, form):
        module = form.save(commit=False)
        module.created_by = self.request.user
        module.project = Project.objects.get(id=self.kwargs["project_id"])
        module.save()
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "listChanged": None,
                        "showMessage": f"New {module.name} added.",
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
    paginate_by = 20

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


class TestCaseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = TestCase
    fields = ["tcname", "module", "sourcedb", "sourcesql", "targetdb", "targetsql", "keycolumns"]
    template_name = "testcase_form.html"

    def form_valid(self, form):
        testcase = form.save(commit=False)
        testcase.created_by = self.request.user
        testcase.project = Project.objects.get(id=self.kwargs["project_id"])
        testcase.save()
        form.save_m2m()
        return redirect("list_testcase", testcase.project.id)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(id=self.kwargs["project_id"])
        context["modules"] = Module.objects.filter(project=self.kwargs["project_id"])
        context["db_connections"] = DbConnection.objects.all()
        return context

    def test_func(self):
        project = Project.objects.get(id=self.kwargs["project_id"])
        if self.request.user in project.members.all():
            return True
        return False

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


class TestCaseListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = TestCase
    template_name = "testcase_list.html"
    paginate_by = 10

    def get_queryset(self):
        return TestCase.objects.filter(project_id=self.kwargs["project_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(id=self.kwargs["project_id"])
        return context

    def test_func(self):
        project = Project.objects.get(id=self.kwargs["project_id"])
        if self.request.user in project.members.all():
            return True
        return False

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


class TestCaseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TestCase
    fields = ["tcname", "module", "sourcedb", "sourcesql", "targetdb", "targetsql", "keycolumns"]
    template_name = "testcase_form.html"

    def form_valid(self, form):
        testcase = form.save(commit=False)
        testcase.modified_by = self.request.user
        testcase.save()
        return redirect("list_testcase", testcase.project.id)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        project_id = self.kwargs.get("project_id")
        testcase_id = self.kwargs.get("testcase_id")
        queryset = queryset.filter(project=project_id, id=testcase_id)
        testcase = queryset.get()
        return testcase

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["db_connections"] = DbConnection.objects.all()
        context["modules"] = Module.objects.filter(project=self.kwargs["project_id"])
        return context

    def test_func(self):
        project = Project.objects.get(id=self.kwargs["project_id"])
        if self.request.user in project.members.all():
            return True
        return False

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


class TestRunCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = TestRun
    template_name = "testrun_form.html"
    fields = ["name"]

    def form_valid(self, form):
        testrun = form.save(commit=False)
        testrun.created_by = self.request.user
        testrun.project = Project.objects.get(id=self.kwargs["project_id"])
        testrun.save()
        form.save_m2m()
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "listChanged": None,
                        "showMessage": f"'{testrun.name}' run created.",
                        "eventType": "created",
                    }
                )
            },
        )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def test_func(self):
        try:
            project = Project.objects.get(id=self.kwargs["project_id"])
            if self.request.user in project.members.all():
                return True
            return False
        except Project.DoesNotExist:
            return redirect(_404_Page)

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


class TestRunListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = TestRun
    template_name = "testrun_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, id=self.kwargs["project_id"])
        context["project"] = project
        testrun_qs = TestRun.objects.prefetch_related("testruncases_set").filter(project=project)
        context["testrun_list"] = testrun_qs
        context["testcases"] = (
            TestRunCases.objects.filter(testrun_id__in=testrun_qs)
            .values("testrun_id", "testcase_status__status_value")
            .annotate(status_count=Count("id"))
        )
        return context

    def test_func(self):
        try:
            project = Project.objects.get(id=self.kwargs["project_id"])
            if self.request.user in project.members.all():
                return True
            return False
        except Project.DoesNotExist:
            return False

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


@login_required
def testrun_index(request, project_id):
    project = Project.objects.get(id=project_id)
    if request.user in project.members.all():
        return render(request, "testruns.html", {"project": project})
    else:
        return render(request, _404_Page)


@login_required
def get_testrun_testcases(request, project_id, testrun_id):
    project = Project.objects.get(id=project_id)
    if request.user in project.members.all():
        testrun_cases = (
            TestRunCases.objects.filter(testrun_id=testrun_id)
            .select_related("testcase_status")
            .select_related("testcases")
        )
        return render(request, "partials/testrun_cases.html", {"testrun_cases": testrun_cases})
    else:
        return render(request, _404_Page)


@login_required
def get_project_testcases(request, project_id, testrun_id):
    project = Project.objects.get(id=project_id)
    testrun = TestRun.objects.get(id=testrun_id)
    testcases = TestCase.objects.filter(project_id=project_id).exclude(id__in=testrun.testcases.all())

    return render(
        request, "partials/select_test_cases.html", {"testcases": testcases, "project": project, "testrun": testrun}
    )


class TestRunDetails(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = TestRun
    template_name = "testrun_detail.html"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        project = get_object_or_404(Project, id=self.kwargs["project_id"])
        testrun = get_object_or_404(TestRun, id=self.kwargs["testrun_id"], project_id=project.id)
        return testrun

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["testcases"] = (
            TestRunCases.objects.filter(testrun=self.get_object())
            .values("testcase_status__status_value")
            .annotate(status_count=Count("id"))
        )
        return context

    def test_func(self):
        testrun_testcase = self.get_object()
        project = testrun_testcase.project
        if self.request.user in project.members.all():
            return True
        return False

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


class TestRunUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TestRun
    fields = ["testcases"]

    def get_object(self, queryset=None):
        testrun = TestRun.objects.get(id=self.kwargs["testrun_id"])
        return testrun

    def test_func(self):
        testrun = self.get_object()
        project = testrun.project
        if self.request.user in project.members.all():
            return True
        return False

    def form_valid(self, form):
        testrun = self.get_object()
        cleaned_tcs = form.cleaned_data["testcases"]
        for item in cleaned_tcs:
            tc_run_id = TestRunCases(testrun_id=testrun.id, testcases_id=item.id)
            if TestRunCases.objects.filter(testcases_id=item.id, testrun_id=testrun.id).count() <= 0:
                tc_run_id.save()
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "listChanged": None,
                        "showMessage": f"{cleaned_tcs.count()} Test Cases were added",
                        "eventType": "created",
                        "removeTCListForm": "True",
                    }
                )
            },
        )

    def form_invalid(self, form) -> HttpResponse:
        return super().form_invalid(form)


class TestRunCaseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = TestRun

    def get_object(self, queryset=None):
        testruncase = TestRunCases.objects.get(id=self.kwargs.get("testcase_id"))
        return testruncase

    def post(self, *args, **kwargs):
        testruncase = self.get_object()
        try:
            self.get_object().delete()
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "listChanged": None,
                            "showMessage": f"{testruncase.testcases.tcname} deleted.",
                            "eventType": "deleted",
                            "refresh": "True",
                        }
                    )
                },
            )
        except ProtectedError as e:
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "listChanged": None,
                            "showMessage": f"Cannot be deleted due to {e}",
                            "eventType": "deleted",
                        }
                    )
                },
            )

    def test_func(self):
        testrun_testcase = self.get_object()
        project = testrun_testcase.testrun.project
        if self.request.user in project.members.all():
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
