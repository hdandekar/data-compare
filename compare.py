import argparse
import pandas as pd
import numpy as np


def report_diff(x):
    """Function to use with groupby.apply to highlight value changes."""
    return x[0] if x[0] == x[1] or pd.isna(x).all() else "{}--->{}".format(x[0], x[1])  # noqa E501
    # f'{x[0]} ---> {x[1]}'


def strip(x):
    """Function to use with applymap to strip whitespaces in a dataframe."""
    return x.strip() if isinstance(x, str) else x


def added_removed(old_df, new_df, old_keys, new_keys):
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
    return out_data


def highlight_differences(value):
    if "--->" in value:
        print()
        color = "orange"
    else:
        color = "white"
    return 'color: %s' % color


def diff_pd(old_df, new_df, idx_col):
    """Identify differences between two pandas DataFrames using a key column.
    Key column is assumed to have only unique data
    (like a database unique id index)
    Args:
        old_df (pd.DataFrame): first dataframe
        new_df (pd.DataFrame): second dataframe
        idx_col (str|list(str)): column name(s) of the index,
          needs to be present in both DataFrames
    """
    # setting the column name as index for fast operations
    old_df = old_df.set_index(idx_col)
    new_df = new_df.set_index(idx_col)

    # get the added and removed rows
    old_keys = old_df.index
    new_keys = new_df.index

    out_data = added_removed(old_df, new_df, old_keys, new_keys)

    # focusing on common data of both dataframes
    common_keys = np.intersect1d(old_keys, new_keys, assume_unique=True)
    common_columns = np.intersect1d(
        old_df.columns, new_df.columns, assume_unique=True
    )
    new_common = new_df.loc[common_keys, common_columns].applymap(strip)
    old_common = old_df.loc[common_keys, common_columns].applymap(strip)
    # get the changed rows keys by dropping identical rows
    # (indexes are ignored, so we'll reset them)
    common_data = pd.concat(
        [old_common.reset_index(), new_common.reset_index()], sort=True
    )
    changed_keys = common_data.drop_duplicates(keep=False)[idx_col]
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

    # using report_diff to merge the changes in a single cell with "-->"
    df_changed = df_all_changes.groupby(level=0, axis=1).apply(
        lambda frame: frame.apply(report_diff, axis=1))
    out_data['changed'] = df_changed
    return out_data


def compare_excel(
        path1, path2, out_path, sheet_name, index_col_name, **kwargs
):

    old_df = pd.read_excel(path1, sheet_name=sheet_name, **kwargs)
    new_df = pd.read_excel(path2, sheet_name=sheet_name, **kwargs)
    diff = diff_pd(old_df, new_df, index_col_name)
    for sname, data in diff.items():
        data.reset_index().to_csv("{}.csv".format(sname),
                                  index=False,
                                  header=True)


def build_parser():
    cfg = argparse.ArgumentParser(
        description="Compares two excel files and outputs the differences "
                    "in another excel file."
    )
    cfg.add_argument("path1", help="Fist excel file")
    cfg.add_argument("path2", help="Second excel file")
    cfg.add_argument("sheetname", help="Name of the sheet to compare.")
    cfg.add_argument(
        "key_column",
        help="Name of the column(s) with unique row identifier. It has to be "
        "the actual text of the first row, not the excel notation."
        "Use multiple times to create a composite index.",
        nargs="+",
    )
    cfg.add_argument("-o", "--output-path", default="compared.xlsx",
                     help="Path of the comparison results")
    cfg.add_argument("--skiprows", help='number of rows to skip', type=int,
                     action='append', default=None)
    return cfg


def main():
    cfg = build_parser()
    opt = cfg.parse_args()
    compare_excel(opt.path1, opt.path2, opt.output_path, opt.sheetname,
                  opt.key_column, skiprows=opt.skiprows)


if __name__ == '__main__':
    main()
