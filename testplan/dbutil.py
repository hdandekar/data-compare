import logging

import mysql.connector
import numpy as np
import pandas as pd
import psycopg
from pandas.errors import DatabaseError

from data_compare.utils.crypto import decrypt_password

logger = logging.getLogger(__name__)


def pg_con(conn):
    cnx = psycopg.connect(
        host=conn.hostname,
        port=conn.portno,
        dbname=conn.dbname,
        user=conn.username,
        password=decrypt_password(conn.password),
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
    try:
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

        common_columns = np.intersect1d(
            old_df.columns, new_df.columns, assume_unique=True
        )

        new_common = new_df.loc[common_keys, common_columns].map(strip)
        old_common = old_df.loc[common_keys, common_columns].map(strip)

        common_data = pd.concat(
            [old_common.reset_index(), new_common.reset_index()], sort=True
        )

        # logger.info("common_data: {}".format(common_data))

        changed_keys = common_data.drop_duplicates(keep=False)[idx_col]
        if isinstance(changed_keys, pd.Series):
            changed_keys = changed_keys.unique()
        else:
            changed_keys = changed_keys.drop_duplicates().set_index(idx_col).index

        df_all_changes = pd.concat(
            [old_common.loc[changed_keys], new_common.loc[changed_keys]],
            axis="columns",
            keys=["old", "new"],
        ).swaplevel(axis="columns")

        df_changed = df_all_changes.T.groupby(level=0).apply(
            lambda frame: frame.apply(report_diff)
        )

        df_changed = df_changed.transpose()
        if not df_changed.empty:
            out_data["changed"] = df_changed
        return {"status": "Executed", "data": out_data}
    except Exception as e:
        logger.error(f"Error Occured {e}")
        return {"status": "Error", "data": e}


def compare_data(srcdf, tgtdf, index_col_name, result_id):
    idx_col = list(index_col_name.split(","))
    if srcdf.index.size != tgtdf.index.size:
        message = "Row Count difference found, Source has {} and Target has {}".format(
            srcdf.index.size, tgtdf.index.size
        )
        return {"status": "Skipped", "message": message}

    diff = diff_pd(srcdf, tgtdf, idx_col)

    if diff["status"] == "Executed":
        if diff["data"]:
            for sname, data in diff["data"].items():
                data.to_csv(f"{result_id}_{sname}.csv", index=True, header=True)
            return {"status": "Fail"}
        else:
            return {"status": "Pass"}
    else:
        return {"status": "Error", "message": diff["data"]}
