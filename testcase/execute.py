# import argparse
# import numpy as np
# from .models import TestCaseResult
# from connection.models import Connection
import mysql.connector
import pandas.io.sql as psql
import pandas as pd
import logging
import sys

logger = logging.getLogger(__name__)


class Comparison(object):

    def report_diff(self, x):
        """Function to use with groupby.apply to highlight value changes."""
        orig = pd.Series(x).values[0]
        mod = pd.Series(x).values[1]
        return orig if orig == mod else '{} ---> {}'.format(orig, mod)

    def strip(self, x):
        """Function to use with applymap to strip whitespaces in dataframe."""
        return x.strip() if isinstance(x, str) else x

    def highlight_differences(self, value):
        if "--->" in value:
            print()
            color = "orange"
        else:
            color = "white"
        return 'color: %s' % color

    def diff_pd(self, old_df, new_df, idx_col):
        logger.info("Starting with diff_pd")
        out_data = {}
        # Drop duplicate rows
        common_rows = pd.merge(old_df, new_df, how='inner')
        logger.info("Completed identifying common_rows for dropping")
        # print("Common:", common_rows)
        old_df = pd.merge(old_df, common_rows,
                          how='outer', indicator=True).query(
            '_merge=="left_only"').drop('_merge', axis=1)
        new_df = pd.merge(new_df, common_rows,
                          how='outer',
                          indicator=True).query(
            '_merge=="left_only"').drop('_merge', axis=1)

        src_only = pd.merge(old_df, new_df, on=idx_col,
                            how='outer', suffixes=('', '_y'), indicator=True)
        src_only = src_only[src_only['_merge']
                            == 'left_only'][old_df.columns]
        logger.info("Completed dropping and building src_only records")
        out_data['dropped'] = src_only.reset_index(drop=True)
        logger.info("Completed dropped records in out_data")
        tgt_only = pd.merge(new_df, old_df, on=idx_col,
                            how='outer', suffixes=('', '_y'), indicator=True)
        tgt_only = tgt_only[tgt_only['_merge']
                            == 'left_only'][new_df.columns]
        logger.info("Completed dropping and building tgt_only records")
        out_data['added'] = tgt_only.reset_index(drop=True)
        logger.info("Completed added records in out_data")

        old_df = pd.merge(old_df, src_only, how='outer', indicator=True).query(
            '_merge=="left_only"').drop('_merge', axis=1)
        logger.info("Completed keeping only the same data in old_df")
        new_df = pd.merge(new_df, tgt_only, how='outer', indicator=True).query(
            '_merge=="left_only"').drop('_merge', axis=1)
        logger.info("Completed keeping only the same data in new_df")
        logger.info("Starting to concat the modified old and new dfs")
        df = pd.concat([old_df, new_df])
        logger.info("Completed concatenation of the records")
        df.set_index(idx_col, inplace=True)
        logger.info("Completed setting the index based on key_columns")
        out_data['changed'] = df.groupby(level=idx_col).agg(self.report_diff)
        logger.info("Completed identifying changed  dataset")
        return out_data

    def compare_data(self, srcdf, tgtdf, index_col_name, id, **kwargs):
        idx_col = list(index_col_name.split(","))
        # logger.info("Source DF memory_usage is: {}".format(
        #     srcdf.memory_usage(index=True).sum()))
        # logger.info("Target DF memory_usage is: {}".format(
        #     tgtdf.memory_usage(index=True).sum()))
        logger.info("Source DF syssize is: {}".format(sys.getsizeof(srcdf)))
        logger.info("Target DF syssize is: {}".format(sys.getsizeof(tgtdf)))
        diff = self.diff_pd(srcdf, tgtdf, idx_col)
        for sname, data in diff.items():
            if sname == 'changed':
                data.reset_index().to_csv("{}_{}.csv".format(id, sname),
                                          index=False,
                                          header=True)
            else:
                data.to_csv("{}_{}.csv".format(id, sname),
                            index=False,
                            header=True)
        logger.info("Completed data comparison test")

    def get_data(self, host, db, user, pwd, sql):
        logger.info("Starting to pulling data from {} database".format(db))
        cnx = mysql.connector.connect(
            host=host,
            database=db,
            user=user,
            password=pwd,
            auth_plugin='mysql_native_password')
        # cursor = cnx.cursor()
        df = psql.read_sql(sql, cnx)
        cnx.close()
        logger.info("Completed pulling data from {} database".format(db))
        return df

    def get_src_data(self, conn, sql):
        host = conn.hostname
        user = conn.username
        pwd = conn.password
        db = conn.dbname
        result_set = self.get_data(host, db, user, pwd, sql)
        return result_set
