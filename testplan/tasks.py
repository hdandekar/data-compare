import logging

from celery import shared_task
from django.shortcuts import get_object_or_404
from django.utils import timezone

from testplan import dbutil
from testplan.models import TestCase, TestRunTestCase, TestRunTestCaseHistory

logger = logging.getLogger(__name__)


TC_FAILED = "Test Case Failed"


@shared_task
def execute_comparison(testrun_tc_history_id, testcase_id, testrun_case_id):
    testruncasehist = get_object_or_404(
        TestRunTestCaseHistory, id=testrun_tc_history_id
    )
    testruncasehist.execution_start = timezone.localtime()
    testcase = get_object_or_404(TestCase, id=testcase_id)

    # Fetch connection details of Source and Target Database.
    src_conn = testcase.sourcedb
    tgt_conn = testcase.targetdb

    src_data = {}
    tgt_data = {}

    try:
        src_data = dbutil.get_data(src_conn, testcase.sourcesql)
    except Exception as error:
        src_data["status"] = "error"
        src_data["message"] = error

    try:
        tgt_data = dbutil.get_data(tgt_conn, testcase.targetsql)
    except Exception as error:
        tgt_data["status"] = "error"
        tgt_data["message"] = error

    if src_data["status"] == "success" and tgt_data["status"] == "success":
        try:
            compare_results = dbutil.compare_data(
                src_data["message"],
                tgt_data["message"],
                testcase.keycolumns.lower(),
                testruncasehist.id,
            )
            testruncasehist.execution_end = timezone.localtime()
            testruncasehist.save()
            if compare_results["status"] == "Fail":
                logger.info(TC_FAILED)
                # Update testcase_run_status_id = Failed(3)
                testruncasehist.testcase_run_status_id = 3
                testruncasehist.comments = (
                    "Differences found between source and target datasets"
                )
                testruncasehist.save()

            if compare_results["status"] == "Pass":
                logger.info("Test Case Passed")
                # Update testcase_run_status_id = Passed(2)
                testruncasehist.testcase_run_status_id = 2
                testruncasehist.comments = (
                    "No differences found between source and target datasets"
                )
                testruncasehist.save()

            if compare_results["status"] == "Skipped":
                logger.info(TC_FAILED)
                # Update testcase_run_status_id = Failed(3)
                testruncasehist.testcase_run_status_id = 5
                testruncasehist.comments = compare_results["message"]
                testruncasehist.save()
            if compare_results["status"] == "Error":
                logger.info(TC_FAILED)
                # Update testcase_run_status_id = Failed(3)
                testruncasehist.testcase_run_status_id = 7
                testruncasehist.comments = compare_results["message"]
                testruncasehist.save()
        except Exception as error:
            logger.error(error)
    else:
        comments = ""
        if src_data["status"] == "error":
            logger.error("Source Data failed: {}".format(src_data["message"]))
            comments += "Source: {}".format(src_data["message"])
        if tgt_data["status"] == "error":
            logger.error("Target Data failed: {}".format(tgt_data["message"]))
            comments += "\nTarget: {}".format(tgt_data["message"])
        # Update testcase_run_status_id = Skipped(5)
        logger.info(f"testruncasehist.comments: {comments}")
        testruncasehist.testcase_run_status_id = 7
        testruncasehist.comments = comments
        testruncasehist.save()
    testrun = TestRunTestCase.objects.get(id=testrun_case_id)
    testrun.testcase_status = testruncasehist.testcase_run_status
    testrun.save()
