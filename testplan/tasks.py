import logging

from celery import shared_task
from django.shortcuts import get_object_or_404
from django.utils import timezone

from testplan import dbutil
from testplan.models import TestCase, TestRunCases, TestRunCasesHistory

logger = logging.getLogger(__name__)


@shared_task
def execute_comparison(testrun_tc_history_id, testcase_id, testrun_case_id):
    print(f"testrun_id: {testrun_case_id}")
    testruncasehist = get_object_or_404(TestRunCasesHistory, id=testrun_tc_history_id)
    testruncasehist.execution_start = timezone.now()
    testcase = get_object_or_404(TestCase, id=testcase_id)

    # Fetch connection details of Source and Target Database.
    src_conn = testcase.sourcedb
    tgt_conn = testcase.targetdb

    src_data = dbutil.get_data(src_conn, testcase.sourcesql)
    tgt_data = dbutil.get_data(tgt_conn, testcase.targetsql)
    logger.info("src_data_status: {} tgt_data_status: {}".format(src_data["status"], tgt_data["status"]))
    if src_data["status"] == "success" and tgt_data["status"] == "success":
        try:
            compare_results = dbutil.compare_data(
                src_data["message"], tgt_data["message"], testcase.keycolumns, testruncasehist.id
            )
            testruncasehist.execution_end = timezone.now()
            testruncasehist.save()
            if compare_results["status"] == "Fail":
                logger.info("Test Case Failed")
                # Update run_status_id = Failed(3)
                testruncasehist.run_status_id = 3
                testruncasehist.comments = "Differences found between source and target datasets"
                testruncasehist.save()

            if compare_results["status"] == "Pass":
                logger.info("Test Case Passed")
                # Update run_status_id = Passed(2)
                testruncasehist.run_status_id = 2
                testruncasehist.comments = "No differences found between source and target datasets"
                testruncasehist.save()
        except Exception as error:
            logger.error("Some error occured")
            logger.error(error)
    else:
        comments = ""
        if src_data["status"] == "error":
            logger.error("Source Data failed: {}".format(src_data["message"]))
            comments += "Source: {}".format(src_data["message"])
            # testruncasehist.save()
        if tgt_data["status"] == "error":
            logger.error("Target Data failed: {}".format(tgt_data["message"]))
            comments += "\nTarget: {}".format(tgt_data["message"])
        # Update run_status_id = Skipped(5)
        logger.info(f"testruncasehist.comments: {comments}")
        testruncasehist.run_status_id = 5
        testruncasehist.comments = comments
        testruncasehist.save()
    testrun = TestRunCases.objects.get(id=testrun_case_id)
    testrun.testcase_status = testruncasehist.run_status
