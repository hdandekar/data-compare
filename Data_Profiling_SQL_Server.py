import pandas as pd
import pyodbc
import pandas_profiling
if __name__ == '__main__':
	cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                        "Server=<HostName>;"
                        "Database=<DB Name>;"
                        "uid=<UserID>;pwd=<Password>")
	Customer = pd.read_sql_query('select * from <Table Name>', cnxn)
	profile=pandas_profiling.ProfileReport(Customer)
	profile.to_file("<Path>\\<Output File Name>.html")