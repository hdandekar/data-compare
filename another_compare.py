import pandas as pd


col_list = ['Country', 'State', 'City']
src_df = pd.read_excel("source.xlsx", sheet_name="Sheet1")

tgt_df = pd.read_excel("target.xlsx", sheet_name="Sheet1")


merge_data = pd.concat([src_df.set_index(col_list), tgt_df.set_index(col_list)], axis='columns',
                       keys=['Source', 'Target'])
# print(merge_data)
removed_duplicates = merge_data.drop_duplicates(keep=False)
print(removed_duplicates)
