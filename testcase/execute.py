import argparse
import numpy as np
from .models import TestCase, TestCaseResult
from connection.models import Connection
import mysql.connector
import pandas.io.sql as psql
import pandas as pd
import sys
import datetime


class Comparison(object):

    def report_diff(self, x):
        """Function to use with groupby.apply to highlight value changes."""
        # return x[0] if x[0] == x[1] or pd.isna(x).all() else "'{}'--->'{}'".format(x[0], x[1])  # noqa E501
        # f'{x[0]} ---> {x[1]}'
        return x[0] if x[0] == x[1] else '{} ---> {}'.format(*x)

    def strip(self, x):
        """Function to use with applymap to strip whitespaces in a dataframe."""
        return x.strip() if isinstance(x, str) else x

    def added_removed(self, old_df, new_df, old_keys, new_keys):
        print("added_removed: ", datetime.datetime.now())
        out_data = {}
        if isinstance(old_keys, pd.MultiIndex):
            removed_keys = old_keys.difference(new_keys)
            added_keys = new_keys.difference(old_keys)
        else:
            removed_keys = np.setdiff1d(old_keys, new_keys)
            added_keys = np.setdiff1d(new_keys, old_keys)
        out_data = {
            'removed': old_df.loc[removed_keys],
            'added': new_df.loc[added_keys]
        }
        print("Fetched added_removed data", datetime.datetime.now())
        return out_data

    def highlight_differences(self, value):
        if "--->" in value:
            print()
            color = "orange"
        else:
            color = "white"
        return 'color: %s' % color

    def another_diff(self, old_df, new_df, idx_col):
        print("Starting with another_diff:", datetime.datetime.now())
        #df_all = pd.concat([old_df.set_index(idx_col), new_df.set_index(idx_col)],
        #                   axis='columns',
        #                   keys=['src', 'tgt'],
        #                   join='outer'
        #                   )
        #df_all = pd.concat([old_df,new_df],axis='columns',keys=['src','tgt'],join='outer')
#        df_all = old_df.merge(new_df, on=idx_col, how='outer', suffixes=('_src','_tgt'))
#        common_rows = old_df.merge(new_df, how='outer',indicator=True).query('_merge=="left_only"').drop('_merge',axis=1)
        common_rows = pd.merge(old_df, new_df, how='outer', suffixes=('','_y'), indicator=True)
        dropped_rows = common_rows[common_rows['_merge']=='left_only'][old_df.columns]
        print("Dropped rows are ")
        print(dropped_rows)
        added_rows = common_rows[common_rows['_merge']=='right_only'][new_df.columns]
        print("Added rows are")
        print(added_rows)
        #print("df_all: ", datetime.datetime.now())
        #print("df_all: ",df_all)
#        df_final = df_all.set_index(idx_col)
#        print("set_index is:")
#        print(df_final.groupby(level=0, axis=1).filter(lambda x: len(x)>1))
        #df_final = df_final.swaplevel(axis='columns')
        #df_final = df_all.swaplevel(axis='columns')[old_df.columns[1:]]
        # print(df_final)
#        print("df_final 1:", datetime.datetime.now())
        ##df_final = df_final.groupby(level=0, axis=1).apply(
            ##lambda frame: frame.apply(self.report_diff, axis=1))
#        print("df_final 2:", datetime.datetime.now())
#        print(df_final)

    def diff_pd(self, old_df, new_df, idx_col):
        """Identify differences between two pandas DataFrames using a key column.
        Key column is assumed to have only unique data
        (like a database unique id index)
        Args:
            old_df (pd.DataFrame): first dataframe
            new_df (pd.DataFrame): second dataframe
            idx_col (str|list(str)): column name(s) of the index,
            needs to be present in both DataFrames
        """
        print("Starting with diff_pd: ", datetime.datetime.now())
        # setting the column name as index for fast operations
        # idx_col = list[col_list.split(",")]
        old_df = old_df.set_index(idx_col)
        new_df = new_df.set_index(idx_col)
        print("Setting the index based on keycolumns: ", datetime.datetime.now())
        # get the added and removed rows
        old_keys = old_df.index
        new_keys = new_df.index

        # out_data = self.added_removed(old_df, new_df, old_keys, new_keys)
        # focusing on common data of both dataframes
        common_keys = np.intersect1d(old_keys, new_keys, assume_unique=True)
        print("common_keys: ", datetime.datetime.now())
        common_columns = np.intersect1d(
            old_df.columns, new_df.columns, assume_unique=True
        )
        print("common_columnes: ", datetime.datetime.now())
        # new_common = new_df.loc[common_keys,
        #                         common_columns].applymap(self.strip)
        # old_common = old_df.loc[common_keys,
        #                         common_columns].applymap(self.strip)
        new_common = new_df.loc[common_keys,
                                common_columns]
        print("new_common:", datetime.datetime.now())
        print("New_Common_data is: ", new_common.head())
        old_common = old_df.loc[common_keys,
                                common_columns]
        print("old_common:", datetime.datetime.now())
        print("New_Common_data is: ", new_common.head())

        print("Setting up new_common,old_common: ", datetime.datetime.now())
        # print("new_common: ", new_common)
        # print("old_common: ", old_common)
        # get the changed rows keys by dropping identical rows
        # (indexes are ignored, so we'll reset them)
        common_data = pd.concat(
            [old_common.reset_index(), new_common.reset_index()], sort=True
        )
        print("common_data:", datetime.datetime.now())
        changed_keys = common_data.drop_duplicates(keep=False)[idx_col]
        print("changed_keys:", datetime.datetime.now())
        if isinstance(changed_keys, pd.Series):
            changed_keys = changed_keys.unique()
        else:
            changed_keys = changed_keys.drop_duplicates().set_index(idx_col).index
        # combining the changed rows via multi level columns
        df_all_changes = pd.concat(
            [old_common.loc[changed_keys], new_common.loc[changed_keys]],
            axis='columns',
            keys=['old', 'new']
        ).swaplevel(axis='columns')
        print("df_all_changes: ", datetime.datetime.now())
        # using report_diff to merge the changes in a single cell with "-->"
        df_changed = df_all_changes.groupby(level=0, axis=1).apply(
            lambda frame: frame.apply(self.report_diff, axis=1))
        print("df_changed: ", datetime.datetime.now())
        out_data['changed'] = df_changed
        print("completed difference in records: ", datetime.datetime.now())
        # return out_data

    def compare_data(self, srcdf, tgtdf, index_col_name, id, **kwargs):
        print("Starting with compare data now: ", datetime.datetime.now())
        idx_col = list(index_col_name.split(","))
        # old_df = srcdf
        # new_df = tgtdf
#        print("old_df is: {}:{}".format(srcdf.memory_usage(index=True).sum(), sys.getsizeof(srcdf)))
#        print("new_df is: {}:{}".format(tgtdf.memory_usage(index=True).sum(), sys.getsizeof(tgtdf)))
        # old_df = pd.read_excel(path1, sheet_name=sheet_name, **kwargs)
        # new_df = pd.read_excel(path2, sheet_name=sheet_name, **kwargs)
        # diff = self.diff_pd(old_df, new_df, idx_col)
        diff = self.another_diff(srcdf, tgtdf, idx_col)
        # for sname, data in diff.items():
        #     data.reset_index().to_csv("{}_{}.csv".format(id, sname),
        #                               index=False,
        #                               header=True)

    def get_data(self, host, db, user, pwd, sql):
        cnx = mysql.connector.connect(
            host=host, database=db, user=user, password=pwd)
        cursor = cnx.cursor()
        df = psql.read_sql(sql, cnx)
        cnx.close()
        return df
        # conn_string = 'mysql://{}:{}@{}/{}'.format(user, pwd, host, db)
        # print("Conn String is:", conn_string)
        # engine = sql.create_engine(conn_string)
        # df = pd.read_sql_query(sql, engine)
        # print(df.head())
        # cursor.execute(sql)
        # rows = cursor.fetchall()
        # return rows

    def get_src_data(self, conn, sql):
        host = conn.hostname
        user = conn.username
        pwd = conn.password
        db = conn.dbname
        query = sql
        result_set = self.get_data(host, db, user, pwd, sql)
        return result_set

        # print("Source host", srcon.hostname)
        # print("Target:", srcon.hostname)
