from django.db import models
from connection.models import Connection


class TestCase(models.Model):
    tcname = models.CharField(max_length=50, blank=False, null=False)
    sourcedbid = models.ForeignKey(Connection, null=True,
                                   on_delete=models.SET_NULL,
                                   related_name='sourcedb')
    sourcesql = models.TextField(max_length=None, null=False, blank=False)
    targetdbid = models.ForeignKey(Connection, null=True,
                                   on_delete=models.SET_NULL,
                                   related_name='targetdb')
    targetsql = models.TextField(max_length=None, null=False, blank=False)
    keycolumns = models.TextField(max_length=None, default="All")

    def __str__(self):
        return str(self.id)


class TestCaseResult(models.Model):
    testcase = models.ForeignKey(TestCase, null=True, on_delete=models.CASCADE)
    summary = models.TextField(max_length=200, blank=True)
    execution_start = models.DateTimeField(auto_now_add=True)
    execution_end = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-execution_end']
