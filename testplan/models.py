from django.contrib.auth import get_user_model
from django.db import models
from django.forms import ValidationError

from data_compare.users.models import User
from project.models import DbConnection, Project


def get_deleted_user_instance():
    return get_user_model().objects.get_or_create(username="deleted")[0]


class TestCaseFolder(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="project_folders"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        related_name="tc_folder_created_by",
        on_delete=models.SET(get_deleted_user_instance),
    )
    modified_by = models.ForeignKey(
        User,
        related_name="tc_folder_modified_by",
        null=True,
        on_delete=models.SET(get_deleted_user_instance),
    )
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="subfolder",
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Checks for presence of root folder, if does not exists allows creation else does not allow"""
        if self.name.lower() == "root":
            if (
                TestCaseFolder.objects.filter(project=self.project, name="root")
                .exclude(pk=self.pk)
                .exists()
            ):
                raise ValidationError(
                    'Folder name "root" is already available in this project.'
                )
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """Set the testcases folder_id to the parent_id of the folder being deleted"""
        if self.parent:
            self.folder_testcases.update(folder=self.parent)
        super().delete(using, keep_parents)


class TestCase(models.Model):
    tcname = models.CharField(max_length=50, blank=False, null=False)
    project = models.ForeignKey(
        Project, related_name="project_testcases", on_delete=models.PROTECT
    )
    sourcedb = models.ForeignKey(
        DbConnection, null=True, on_delete=models.PROTECT, related_name="sourcedb"
    )
    sourcesql = models.TextField(max_length=None, null=False, blank=False)
    targetdb = models.ForeignKey(
        DbConnection, null=True, on_delete=models.PROTECT, related_name="targetdb"
    )
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
    folder = models.ForeignKey(
        TestCaseFolder, on_delete=models.CASCADE, related_name="folder_testcases"
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return str(self.id)


class TestCaseStatus(models.Model):
    status_value = models.CharField(max_length=255)


class TestRun(models.Model):
    testcases = models.ManyToManyField(TestCase, blank=True, through="TestRunTestCase")
    project = models.ForeignKey(
        Project, related_name="project_testruns", on_delete=models.PROTECT
    )
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
    testcase_status = models.ForeignKey(
        TestCaseStatus, null=True, default=1, on_delete=models.PROTECT
    )


class TestRunTestCaseHistory(models.Model):
    testrun_testcase = models.ForeignKey(
        TestRunTestCase,
        on_delete=models.CASCADE,
        related_name="testrun_testcase_history",
    )
    testcase_run_status = models.ForeignKey(
        TestCaseStatus, null=True, default=1, on_delete=models.PROTECT
    )
    testrun = models.ForeignKey(
        TestRun, on_delete=models.CASCADE, related_name="history_test_run", blank=True
    )
    testcase = models.ForeignKey(
        TestCase, on_delete=models.CASCADE, related_name="history_test_run", blank=True
    )
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
        ordering = ["-id"]
