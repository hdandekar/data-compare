import json
import logging

import pandas as pd
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models.aggregates import Count
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)

from project.models import DbConnection
from testplan import tasks
from testplan.decorators import user_is_member
from testplan.mixins import AdminPermissionMixin, MemberPermissionMixin
from testplan.models import (
    Project,
    TestCase,
    TestCaseFolder,
    TestRun,
    TestRunTestCase,
    TestRunTestCaseHistory,
)
from testplan.utils import build_hierarchy

_404_Page = "404.html"

logger = logging.getLogger(__name__)


class TestCaseCreateView(LoginRequiredMixin, MemberPermissionMixin, CreateView):
    model = TestCase
    fields = [
        "tcname",
        "sourcedb",
        "sourcesql",
        "targetdb",
        "targetsql",
        "keycolumns",
        "folder",
    ]
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
        context["db_connections"] = DbConnection.objects.filter(
            project_id=self.kwargs["project_id"]
        )
        context["folders"] = context["project"].project_folders.all()
        return context

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.kwargs.get("project_id")
        project = Project.objects.get(id=project_id)
        initial["project"] = project
        return initial

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)

    def get_form(self, instance=None):
        form = super().get_form()
        all_folders = TestCaseFolder.objects.filter(
            project_id=self.kwargs["project_id"]
        )
        hierarchy = build_hierarchy(all_folders)
        # Creating choices with indented names based on hierarchy level
        choices = [
            (folder.id, "--" * level + " " + folder.name) for folder, level in hierarchy
        ]
        form.fields["folder"].choices = choices
        return form


class TestCaseUpdateView(LoginRequiredMixin, MemberPermissionMixin, UpdateView):
    model = TestCase
    fields = [
        "tcname",
        "sourcedb",
        "sourcesql",
        "targetdb",
        "targetsql",
        "keycolumns",
        "folder",
    ]
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
        queryset = queryset.select_related("sourcedb", "targetdb").filter(
            project=project_id, id=testcase_id
        )
        testcase = queryset.get()
        return testcase

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["db_connections"] = DbConnection.objects.filter(
            project_id=self.kwargs["project_id"]
        )
        return context

    def get_form(self, instance=None):
        form = super().get_form()
        all_folders = TestCaseFolder.objects.filter(
            project_id=self.kwargs["project_id"]
        )
        hierarchy = build_hierarchy(all_folders)
        # Creating choices with indented names based on hierarchy level
        choices = [
            (folder.id, "--" * level + " " + folder.name) for folder, level in hierarchy
        ]
        form.fields["folder"].choices = choices
        return form

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


class TestRunCreateView(LoginRequiredMixin, MemberPermissionMixin, CreateView):
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

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


class TestCaseDeleteView(LoginRequiredMixin, MemberPermissionMixin, DeleteView):
    model = TestCase

    def post(self, *args, **kwargs):
        testcase = TestCase.objects.get(id=self.kwargs["testcase_id"])
        try:
            testcase.delete()
            return HttpResponse(
                status=200,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "showMessage": f"'{testcase.tcname}' deleted successfully",
                            "eventType": "deleted",
                        }
                    ),
                },
            )
            return
        except ProtectedError as e:
            logger.error(f"Cannot delete {testcase.tcname} due to {e}")
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "listChanged": None,
                            "showMessage": f"'{testcase.tcname}' cannot be deleted",
                            "eventType": "deleted",
                        }
                    )
                },
            )

    def handle_no_permission(self):
        testcase = TestCase.objects.get(id=self.kwargs["testcase_id"])
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "showMessage": f"You do not have permission to delete '{testcase.tcname}'",
                        "eventType": "permissionDenied",
                    }
                )
            },
        )


class TestRunListView(LoginRequiredMixin, MemberPermissionMixin, ListView):
    """
    List of Test Runs for a Project
    """

    model = TestRun
    template_name = "testrun_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, id=self.kwargs["project_id"])
        context["project"] = project
        testrun_qs = TestRun.objects.prefetch_related("testruntestcase_set").filter(
            project=project
        )
        context["testrun_list"] = testrun_qs
        context["testcases"] = (
            TestRunTestCase.objects.filter(testrun_id__in=testrun_qs)
            .values("testrun_id", "testcase_status__status_value")
            .annotate(status_count=Count("id"))
        )
        return context

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


@require_http_methods(["GET"])
@login_required
@user_is_member
def testrun_index(request, project_id):
    """
    Test Run Index Page which in turn calls TestRunListView to render the list of testruns.
    """
    project = Project.objects.get(id=project_id)
    if request.user in project.members.all():
        return render(request, "testruns_index.html", {"project": project})
    else:
        return render(request, _404_Page)


@require_http_methods(["GET"])
@login_required
@user_is_member
def get_testrun_testcases(request, project_id, testrun_id):
    """
    Get Test Run Test Cases for a Test Run
    """
    project = Project.objects.get(id=project_id)
    latest_testcase_runs = []
    most_recent_testcase_runs = []

    if request.user in project.members.all():
        testrun_cases = TestRunTestCase.objects.filter(testrun_id=testrun_id)

        for rn in testrun_cases:
            try:
                most_recent_tc_run = TestRunTestCaseHistory.objects.filter(
                    testrun_testcase_id=rn.id
                ).latest("id")
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
                latest_testcase_run = TestRunTestCaseHistory.objects.filter(
                    testrun_testcase_id=run.id
                ).latest("id")
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


@require_http_methods(["GET"])
@login_required
@user_is_member
def get_project_testcases(request, project_id, testrun_id):
    project = Project.objects.get(id=project_id)
    testrun = TestRun.objects.get(id=testrun_id)
    testcases = TestCase.objects.filter(project_id=project_id).exclude(
        id__in=testrun.testcases.all()
    )

    return render(
        request,
        "partials/select_test_cases.html",
        {"testcases": testcases, "project": project, "testrun": testrun},
    )


class TestRunDetails(LoginRequiredMixin, MemberPermissionMixin, DetailView):
    model = TestRun
    template_name = "testrun_detail.html"

    def get_object(self, queryset=None):
        project = get_object_or_404(Project, id=self.kwargs["project_id"])
        testrun = get_object_or_404(
            TestRun, id=self.kwargs["testrun_id"], project_id=project.id
        )
        return testrun

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["testcases"] = (
            TestRunTestCase.objects.filter(testrun=self.get_object())
            .values("testcase_status__status_value")
            .annotate(status_count=Count("id"))
        )
        return context

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


class TestRunUpdateView(LoginRequiredMixin, MemberPermissionMixin, UpdateView):
    """
    Update the Test Run by including more Test Cases.
    """

    model = TestRun
    fields = ["testcases"]

    def get_object(self, queryset=None):
        testrun = TestRun.objects.get(id=self.kwargs["testrun_id"])
        return testrun

    def form_valid(self, form):
        testrun = self.get_object()
        cleaned_tcs = form.cleaned_data["testcases"]
        for item in cleaned_tcs:
            testrun_testcase = TestRunTestCase(
                testrun_id=testrun.id, testcase_id=item.id
            )
            if (
                TestRunTestCase.objects.filter(
                    testcase_id=item.id, testrun_id=testrun.id
                ).count()
                <= 0
            ):
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


class TestRunCaseDeleteView(LoginRequiredMixin, AdminPermissionMixin, DeleteView):
    """
    Delete a Test Case from the Test Run, in case of AdminPermission returning False
    then PermissionDenied message is sent as response to the client.
    """

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

    def handle_no_permission(self):
        testrun_testcase = self.get_object()
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "showMessage": f"You do not have permission to delete '{testrun_testcase.testcase.tcname}'",
                        "eventType": "permissiondenied",
                    }
                )
            },
        )


require_http_methods(["POST"])


@login_required
@user_is_member
def execute_testcase(request, project_id, testrun_id, testrun_testcase_id):
    """
    Initiates execution of the test case in a test run, not adding decorator to check  `user_is_member`
    as permissionDenied message is sent as response to the client.
    """
    project = Project.objects.get(id=project_id)
    if request.user in project.members.all():
        testrun = TestRun.objects.get(id=testrun_id)
        testrun_testcase = TestRunTestCase.objects.get(
            testrun_id=testrun.id, id=testrun_testcase_id
        )

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
        tasks.execute_comparison.delay(
            testrun_tc_history.id, testcase.id, testrun_testcase.id
        )

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


@require_http_methods(["GET"])
@login_required
@user_is_member
def testrun_testcase_history_list(request, project_id, testrun_id, testrun_testcase_id):
    """
    Lists testcases history for a testrun
    """
    project = Project.objects.get(id=project_id)
    testrun = TestRun.objects.get(id=testrun_id)
    testrun_testcase = TestRunTestCase.objects.get(id=testrun_testcase_id)
    testcase_run_history = TestRunTestCaseHistory.objects.select_related(
        "testcase_run_status", "triggered_by"
    ).filter(testrun_testcase_id=testrun_testcase_id)
    if request.user in project.members.all():
        return render(
            request,
            "testrun_testcase_history_list.html",
            {
                "testcase_run_history": testcase_run_history,
                "project": project,
                "testrun": testrun,
                "testrun_testcase": testrun_testcase,
                "testcase": testrun_testcase.testcase,
            },
        )
    else:
        messages.error(
            request, "Permission denied to view ,please contact your project owner"
        )
        return redirect("testrun_detail", project_id=project_id, testrun_id=testrun_id)


@require_http_methods(["GET"])
@login_required
@user_is_member
def testrun_case_result_summary(
    request, project_id, testrun_id, testrun_case_id, testrun_case_history_id
):
    project = Project.objects.get(id=project_id)
    testrun = TestRun.objects.get(id=testrun_id)
    testrun_testcase = TestRunTestCase.objects.get(id=testrun_case_id)
    test_case = TestCase.objects.get(id=testrun_testcase.testcase_id)
    if TestRunTestCaseHistory.objects.filter(
        testrun_testcase_id=testrun_case_id
    ).exists():
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
            "testrun_testcase_history_testcase_result.html",
            {
                "added": added_set,
                "added_data": added_data,
                "removed": removed_set,
                "removed_data": removed_data,
                "changed": changed_set,
                "changed_data": changed_data,
                "test_case": test_case,
                "project": project,
                "testrun": testrun,
                "testrun_testcase": testrun_testcase,
            },
        )
    else:
        return render(
            request,
            "testrun_testcase_history_testcase_result.html",
            {
                "message": "History Not Available",
                "test_case": test_case,
                "project": project,
                "testrun": testrun,
                "testrun_testcase": testrun_testcase,
            },
        )


class TestCaseFolderIndexView(LoginRequiredMixin, MemberPermissionMixin, ListView):
    model = TestCaseFolder
    template_name = "testcase_list.html"
    context_object_name = "root_folders"

    def get_queryset(self):
        project = Project.objects.get(id=self.kwargs["project_id"])
        try:
            root = TestCaseFolder.objects.get(
                name="root", project_id=self.kwargs["project_id"], parent__isnull=True
            )
            return TestCaseFolder.objects.filter(
                project_id=self.kwargs["project_id"], parent_id=root.id
            ).select_related()
        except ObjectDoesNotExist as e:
            logger.info(f"Creating root folder for 1st time, error is {e}")
            root = TestCaseFolder.objects.create(
                name="root",
                project_id=self.kwargs["project_id"],
                created_by=project.owner,
            )
            return TestCaseFolder.objects.filter(
                project_id=self.kwargs["project_id"], parent_id=root.id
            ).select_related()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(id=self.kwargs["project_id"])
        context["all_test_cases"] = TestCase.objects.select_related(
            "sourcedb", "targetdb"
        ).filter(project_id=self.kwargs["project_id"])
        return context

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


class TestCaseFolderSubfoldersView(
    LoginRequiredMixin, MemberPermissionMixin, DetailView
):
    model = TestCaseFolder
    template_name = "partials/folder_subfolder.html"
    context_object_name = "folder"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = get_object_or_404(Project, id=self.kwargs["project_id"])
        context["subfolders"] = (
            self.object.subfolder.select_related("parent")
            .all()
            .exclude(name="root", parent__isnull=True)
        )
        test_cases = self.get_all_test_cases(self.object)
        context["test_cases"] = test_cases
        return context

    def get_all_test_cases(self, folder):
        """
        Recursively gather test cases from the folder and its subfolders.
        """
        test_cases = list(
            folder.folder_testcases.select_related("sourcedb", "targetdb").filter(
                project_id=self.kwargs["project_id"]
            )
        )
        return test_cases

    def handle_no_permission(self) -> HttpResponseRedirect:
        return render(self.request, _404_Page)


class TestCaseFolderCreateView(LoginRequiredMixin, MemberPermissionMixin, CreateView):
    model = TestCaseFolder
    template_name = "testfolder_form.html"
    fields = ["name", "parent"]

    def get_form(self):
        form = super().get_form()
        form.fields["parent"].queryset = TestCaseFolder.objects.filter(
            project_id=self.kwargs["project_id"]
        )
        all_folders = TestCaseFolder.objects.filter(
            project_id=self.kwargs["project_id"]
        )
        hierarchy = build_hierarchy(all_folders)
        choices = [
            (folder.id, "--" * level + " " + folder.name) for folder, level in hierarchy
        ]
        form.fields["parent"].choices = choices
        return form

    def form_valid(self, form):
        tc_folder = form.save(commit=False)
        tc_folder.created_by = self.request.user
        tc_folder.project = Project.objects.get(id=self.kwargs["project_id"])
        try:
            tc_folder.save()
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "listChanged": None,
                            "showMessage": f"{tc_folder.name} added.",
                            "eventType": "created",
                        }
                    )
                },
            )
        except forms.ValidationError as e:
            logger.error(f"Error Occured {e}")
            form.add_error("name", e)
            return self.form_invalid(form)


class TestCaseFolderUpdateView(LoginRequiredMixin, MemberPermissionMixin, View):
    model = TestCaseFolder

    def get_object(self):
        project_id = self.kwargs.get("project_id")
        folder_id = self.kwargs.get("folder_id")
        folder = TestCaseFolder.objects.get(project_id=project_id, id=folder_id)
        return folder

    def get_descendants(self, folder):
        descendants = set()
        children = TestCaseFolder.objects.filter(parent=folder)
        for child in children:
            descendants.add(child.id)
            descendants.update(self.get_descendants(child))
        return descendants

    def get_form(self, data=None, instance=None):
        class TempForm(forms.ModelForm):
            class Meta:
                model = TestCaseFolder
                fields = ["name", "parent"]

        form = TempForm(data, instance=instance)
        exclude_ids = {instance.id} if instance else set()
        if instance:
            exclude_ids.update(self.get_descendants(instance))
        form.fields["parent"].queryset = TestCaseFolder.objects.filter(
            project_id=self.kwargs["project_id"]
        ).exclude(id__in=exclude_ids)

        all_folders = TestCaseFolder.objects.filter(
            project_id=self.kwargs["project_id"]
        ).exclude(id__in=exclude_ids)

        hierarchy = build_hierarchy(all_folders)
        # Creating choices with indented names based on hierarchy level
        choices = [
            (folder.id, "--" * level + " " + folder.name) for folder, level in hierarchy
        ]
        form.fields["parent"].choices = choices
        return form

    def get(self, request, project_id, folder_id):
        folder = get_object_or_404(TestCaseFolder, project_id=project_id, id=folder_id)
        form = self.get_form(instance=folder)
        csrf_token = get_token(request)
        return render(
            request,
            "testfolder_form.html",
            {"csrf_token": csrf_token, "object": folder, "form": form},
        )

    def post(self, request, project_id, folder_id):
        folder = get_object_or_404(TestCaseFolder, project_id=project_id, id=folder_id)
        if "delete" in request.POST:
            return self.delete(request, project_id, folder_id)
        form = self.get_form(data=request.POST, instance=folder)

        if form.is_valid():
            tc_folder = form.save(commit=False)
            tc_folder.modified_by = self.request.user
            tc_folder.project = Project.objects.get(id=self.kwargs["project_id"])
            try:
                tc_folder.save()
                messages.success(request, f"{tc_folder.name} updated successfully'")
                return HttpResponse(
                    status=201,
                    headers={
                        "HX-Trigger": json.dumps(
                            {
                                "listChanged": None,
                                "showMessage": f"{tc_folder.name} updated",
                                "eventType": "updated",
                            }
                        ),
                        "HX-Refresh": "true",
                    },
                )
            except forms.ValidationError as e:
                logger.error(f"Error Occured {e}")
                form.add_error("name", e)
                return self.form_invalid(form)

    def form_invalid(self, form):
        return render(
            self.request,
            "testfolder_form.html",
            {"form": form, "object": self.get_object()},
        )

    def delete(self, request, project_id, folder_id):
        folder = get_object_or_404(TestCaseFolder, project_id=project_id, id=folder_id)
        try:
            folder.delete()
            messages.warning(
                request,
                f"{folder.name} deleted successfully, all its testcases are moved to {folder.parent} folder",
            )
            return HttpResponse(
                status=201,
                headers={"HX-Refresh": "true"},
            )
        except Exception as error:
            logger.error(f"error is {error}")
            messages.error(
                request,
                f"Something went wrong in deleting the folder {folder}, our engineers have been notified",
            )
            return HttpResponse(
                status=400,
                headers={"HX-Refresh": "true"},
            )
