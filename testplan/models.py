from django.contrib.auth import get_user_model
from django.db import models

from data_compare.users.models import User
from project.models import DbConnection, Project


def get_deleted_user_instance():
    return get_user_model().objects.get_or_create(username="deleted")[0]


class TestCase(models.Model):
    tcname = models.CharField(max_length=50, blank=False, null=False)
    project = models.ForeignKey(Project, related_name="project_testcases", on_delete=models.PROTECT)
    sourcedb = models.ForeignKey(DbConnection, null=True, on_delete=models.PROTECT, related_name="sourcedb")
    sourcesql = models.TextField(max_length=None, null=False, blank=False)
    targetdb = models.ForeignKey(DbConnection, null=True, on_delete=models.PROTECT, related_name="targetdb")
    targetsql = models.TextField(max_length=None, null=False, blank=False)
    keycolumns = models.TextField(max_length=None, default="All")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        related_name="testcase_created_by",
        on_delete=models.SET(get_deleted_user_instance),
    )
    modified_by = models.ForeignKey(
        User,
        related_name="testcase_modified_by",
        null=True,
        on_delete=models.SET(get_deleted_user_instance),
    )

    def __str__(self):
        return str(self.id)


class TestCaseStatus(models.Model):
    status_value = models.CharField(max_length=255)


class TestRun(models.Model):
    testcases = models.ManyToManyField(TestCase, blank=True, through="TestRunTestCase")
    project = models.ForeignKey(Project, related_name="project_testruns", on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        User,
        related_name="testrun_created_by",
        on_delete=models.SET(get_deleted_user_instance),
    )
    modified_by = models.ForeignKey(
        User,
        related_name="testrun_modified_by",
        null=True,
        on_delete=models.SET(get_deleted_user_instance),
    )
    created_date = models.DateTimeField(auto_now_add=True)
    closed_date = models.DateField(null=True)


class TestRunTestCase(models.Model):
    testcase = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    testrun = models.ForeignKey(TestRun, on_delete=models.CASCADE)
    testcase_status = models.ForeignKey(TestCaseStatus, null=True, default=1, on_delete=models.PROTECT)


class TestRunTestCaseHistory(models.Model):
    testrun_testcase = models.ForeignKey(
        TestRunTestCase, on_delete=models.CASCADE, related_name="testrun_testcase_history"
    )
    testcase_run_status = models.ForeignKey(TestCaseStatus, null=True, default=1, on_delete=models.PROTECT)
    testrun = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name="history_test_run", blank=True)
    testcase = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name="history_test_run", blank=True)
    execution_start = models.DateTimeField(null=True)
    execution_end = models.DateTimeField(null=True)
    task_id = models.CharField(max_length=255)
    comments = models.TextField(blank=True)
    triggered_by = models.ForeignKey(
        User,
        related_name="testrun_history_triggered_by",
        on_delete=models.SET(get_deleted_user_instance),
    )

    class Meta:
        ordering = ["-execution_end"]
