import json
import logging

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models.aggregates import Count
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from project.models import DbConnection
from testplan import tasks
from testplan.models import Project, TestCase, TestRun, TestRunTestCase, TestRunTestCaseHistory

_404_Page = "404.html"

logger = logging.getLogger(__name__)


class TestCaseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = TestCase
    fields = ["tcname", "sourcedb", "sourcesql", "targetdb", "targetsql", "keycolumns"]
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
    fields = ["tcname", "sourcedb", "sourcesql", "targetdb", "targetsql", "keycolumns"]
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
        testrun_qs = TestRun.objects.prefetch_related("testruntestcase_set").filter(project=project)
        context["testrun_list"] = testrun_qs
        context["testcases"] = (
            TestRunTestCase.objects.filter(testrun_id__in=testrun_qs)
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
    latest_testcase_runs = []
    most_recent_testcase_runs = []

    if request.user in project.members.all():
        testrun_cases = TestRunTestCase.objects.filter(testrun_id=testrun_id)

        for rn in testrun_cases:
            try:
                most_recent_tc_run = TestRunTestCaseHistory.objects.filter(testrun_testcase_id=rn.id).latest("id")
                most_recent_testcase_runs.append(
                    {
                        "testrun_testcase": rn,
                        "most_recent_testcase_run": most_recent_tc_run,
                    }
                )
            except Exception:
                most_recent_testcase_runs.append(
                    {
                        "testrun_testcase": rn,
                        "most_recent_testcase_run": None,
                    }
                )

        for run in testrun_cases:
            try:
                latest_testcase_run = TestRunTestCaseHistory.objects.filter(testrun_testcase_id=run.id).latest("id")
                latest_testcase_runs.append(latest_testcase_run)
            except Exception:
                latest_testcase_runs.append(None)
        return render(
            request,
            "partials/testrun_cases.html",
            {
                "testrun_cases": testrun_cases,
                "testcase_run_history": latest_testcase_runs,
                "most_recent_testcase_runs": most_recent_testcase_runs,
            },
        )
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
        project = get_object_or_404(Project, id=self.kwargs["project_id"])
        testrun = get_object_or_404(TestRun, id=self.kwargs["testrun_id"], project_id=project.id)
        return testrun

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["testcases"] = (
            TestRunTestCase.objects.filter(testrun=self.get_object())
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
            testrun_testcase = TestRunTestCase(testrun_id=testrun.id, testcase_id=item.id)
            if TestRunTestCase.objects.filter(testcase_id=item.id, testrun_id=testrun.id).count() <= 0:
                testrun_testcase.save()
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
        testruncase = TestRunTestCase.objects.get(id=self.kwargs.get("testcase_id"))
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
                            "showMessage": f"{testruncase.testcase.tcname} deleted.",
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


@login_required
def execute_testcase(request, project_id, testrun_id, testrun_testcase_id):
    project = Project.objects.get(id=project_id)
    if request.user in project.members.all():
        testrun = TestRun.objects.get(id=testrun_id)
        testrun_testcase = TestRunTestCase.objects.get(testrun_id=testrun.id, id=testrun_testcase_id)

        testrun_tc_history = TestRunTestCaseHistory(
            testrun_testcase=testrun_testcase,
            testrun=testrun,
            testcase_id=testrun_testcase.testcase_id,
            testcase_run_status_id=6,
            triggered_by=request.user,
        )
        testrun_tc_history.save()
        logger.info(f"Test Run TC History Save {testrun_tc_history.id}")
        testcase = get_object_or_404(TestCase, id=testrun_testcase.testcase_id)

        # tasks.execute_comparison(testrun_tc_history.id, testcase.id, testrun_testcase.id)
        tasks.execute_comparison.delay(testrun_tc_history.id, testcase.id, testrun_testcase.id)

        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "listChanged": None,
                        "showMessage": "Test Case execution started",
                        "eventType": "triggerd",
                    }
                )
            },
        )
    else:
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "showMessage": "Permission denied for execution,please contact your project owner",
                        "eventType": "permissiondenied",
                    }
                )
            },
        )


@login_required
def testrun_history(request, project_id, testrun_id, testrun_testcase_id):
    project = Project.objects.get(id=project_id)
    testrun = TestRun.objects.get(id=testrun_id)
    testrun_testcase = TestRunTestCase.objects.get(id=testrun_testcase_id)

    # testcase_run_history = TestRunCasesHistory.objects.filter(testrun_testcase_id=testrun_case_id).order_by(
    #     "-execution_end"
    # )
    testcase_run_history = TestRunTestCaseHistory.objects.select_related("testcase_run_status", "triggered_by").filter(
        testrun_testcase_id=testrun_testcase_id
    )
    if request.user in project.members.all():
        return render(
            request,
            "testrun_history.html",
            {
                "testcase_run_history": testcase_run_history,
                "project": project,
                "testrun": testrun,
                "testrun_testcase": testrun_testcase,
                "testcase": testrun_testcase.testcase,
            },
        )
    else:
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "showMessage": "Permission denied to view ,please contact your project owner",
                        "eventType": "permissiondenied",
                    }
                )
            },
        )


@login_required
def testrun_case_result_summary(request, project_id, testrun_id, testrun_case_id, testrun_case_history_id):
    project = Project.objects.get(id=project_id)
    testrun = TestRun.objects.get(id=testrun_id)
    testrun_testcase = TestRunTestCase.objects.get(id=testrun_case_id)
    test_case = TestCase.objects.get(id=testrun_testcase.testcase_id)
    if TestRunTestCaseHistory.objects.filter(testrun_testcase_id=testrun_case_id).exists():
        try:
            added_data = pd.read_csv(f"{testrun_case_history_id}_added.csv")
            added_set = added_data.to_numpy()
        except Exception as e:
            added_data = None
            added_set = None
            logger.info(f"Added file not present: {e}")

        try:
            removed_data = pd.read_csv(f"{testrun_case_history_id}_removed.csv")
            removed_set = removed_data.to_numpy()
        except Exception as e:
            removed_data = None
            removed_set = None
            logger.info(f"Removed file not present: {e}")
        try:
            changed_data = pd.read_csv(f"{testrun_case_history_id}_changed.csv")
            changed_set = changed_data.to_numpy()
        except Exception as e:
            changed_data = None
            changed_set = None
            logger.info(f"Changed file not present: {e}")

        return render(
            request,
            "testrun_history_result.html",
            {
                "added": added_set,
                "added_data": added_data,
                "removed": removed_set,
                "removed_data": removed_data,
                "changed": changed_set,
                "changed_data": changed_data,
                "test_case": test_case,
                "testrun_testcase": testrun_testcase,
                "project": project,
                "testrun": testrun,
                "testrun_testcase": testrun_testcase,
            },
        )
    else:
        return render(
            request,
            "testrun_history_result.html",
            {
                "message": "History Not Available",
                "test_case": test_case,
                "testrun_testcase": testrun_testcase,
                "project": project,
                "testrun": testrun,
                "testrun_testcase": testrun_testcase,
            },
        )
