import logging

import mysql.connector
import numpy as np
import pandas as pd
import psycopg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from pandas.errors import DatabaseError

from testplan.models import TestCase, TestRunCases, TestRunCasesHistory

logger = logging.getLogger(__name__)


def execute_comparison(testrun_tc_history_id, testcase_id, testrun_case_id):
    print(f"testrun_id: {testrun_case_id}")
    testruncasehist = get_object_or_404(TestRunCasesHistory, id=testrun_tc_history_id)
    testruncasehist.execution_start = timezone.now()
    testcase = get_object_or_404(TestCase, id=testcase_id)

    # Fetch connection details of Source and Target Database.
    src_conn = testcase.sourcedb
    tgt_conn = testcase.targetdb

    src_data = get_data(src_conn, testcase.sourcesql)
    tgt_data = get_data(tgt_conn, testcase.targetsql)
    logger.info("src_data_status: {} tgt_data_status: {}".format(src_data["status"], tgt_data["status"]))
    if src_data["status"] == "success" and tgt_data["status"] == "success":
        try:
            compare_results = compare_data(
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
    testrun.save()


def pg_con(conn):
    cnx = psycopg.connect(
        host=conn.hostname,
        port=conn.portno,
        dbname=conn.dbname,
        user=conn.username,
        password=conn.password,
    )
    return cnx


def mysql_con(conn):
    cnx = mysql.connector.connect(
        host=conn.hostname,
        port=conn.portno,
        database=conn.dbname,
        user=conn.username,
        password=conn.password,
        auth_plugin="mysql_native_password",
    )
    return cnx


def get_data(conn, sql):
    cnx = None
    try:
        if conn.dbtype.dbname.lower() == "postgresql":
            cnx = pg_con(conn)
        if conn.dbtype.dbname.lower() == "mysql":
            cnx = mysql_con(conn)
        df = pd.read_sql_query(sql, cnx)
        df = df.fillna("Blank")
        cnx.close()
        logger.info(f"Completed pulling data from {conn.dbname} database")
        return {"status": "success", "message": df}
    except DatabaseError as error:
        return {"status": "error", "message": error}


def report_diff(x):
    """Function to use with groupby.apply to highlight value changes."""
    orig = pd.Series(x).values[0]
    mod = pd.Series(x).values[1]
    return orig if orig == mod else f"{orig} ---> {mod}"


def strip(x):
    """Function to use with applymap to strip whitespaces in dataframe."""
    return x.strip() if isinstance(x, str) else x


def diff_pd(old_df, new_df, idx_col):
    """
    Identify differences between two pandas DataFrames using a key column.
    Key column is assumed to have a unique row identifier, i.e. no duplicates.
    """
    old_df = old_df.set_index(idx_col)
    new_df = new_df.set_index(idx_col)
    old_keys = old_df.index
    new_keys = new_df.index
    if isinstance(old_keys, pd.MultiIndex):
        removed_keys = old_keys.difference(new_keys)
        added_keys = new_keys.difference(old_keys)
    else:
        removed_keys = np.setdiff1d(old_keys, new_keys)
        added_keys = np.setdiff1d(new_keys, old_keys)
    out_data = {}
    removed = old_df.loc[removed_keys]
    if not removed.empty:
        out_data["removed"] = removed
    added = new_df.loc[added_keys]

    if not added.empty:
        out_data["added"] = added

    common_keys = np.intersect1d(old_keys, new_keys, assume_unique=True)

    common_columns = np.intersect1d(old_df.columns, new_df.columns, assume_unique=True)

    new_common = new_df.loc[common_keys, common_columns].map(strip)
    old_common = old_df.loc[common_keys, common_columns].map(strip)

    common_data = pd.concat([old_common.reset_index(), new_common.reset_index()], sort=True)

    # logger.info("common_data: {}".format(common_data))

    changed_keys = common_data.drop_duplicates(keep=False)[idx_col]
    if isinstance(changed_keys, pd.Series):
        changed_keys = changed_keys.unique()
    else:
        changed_keys = changed_keys.drop_duplicates().set_index(idx_col).index

    df_all_changes = pd.concat(
        [old_common.loc[changed_keys], new_common.loc[changed_keys]], axis="columns", keys=["old", "new"]
    ).swaplevel(axis="columns")

    df_changed = df_all_changes.T.groupby(level=0).apply(lambda frame: frame.apply(report_diff))

    df_changed = df_changed.transpose()
    if not df_changed.empty:
        out_data["changed"] = df_changed
    # logger.info("OUT_DATA is: {}".format(out_data))
    return out_data


def compare_data(srcdf, tgtdf, index_col_name, result_id):
    idx_col = list(index_col_name.split(","))
    diff = diff_pd(srcdf, tgtdf, idx_col)
    if diff:
        for sname, data in diff.items():
            data.to_csv(f"{result_id}_{sname}.csv", index=True, header=True)
        return {"status": "Fail"}
    else:
        logger.info("Diff is absent")
        return {"status": "Pass"}
