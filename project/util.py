import psycopg
from mysql import connector as mysql_connector


def check_db_connection(dbtype, dbname, username, password, portno, **kwargs):
    hostname = kwargs["hostname"]
    if dbtype.lower() == "postgresql":
        connection_status = check_pgsql(dbname, username, password, hostname, portno)
        return connection_status
    if dbtype.lower() == "mysql":
        connection_status = check_mysql_conn(dbname, username, password, hostname, portno)
        return connection_status


def check_pgsql(dbname, uname, pwd, hostname, portno):
    try:
        cnx = psycopg.connect(
            host=hostname,
            port=portno,
            dbname=dbname,
            user=uname,
            password=pwd,
        )
        return {"connected": True, "connection": cnx}
    except psycopg.Error as err:
        return {"connected": False, "error": err}


def check_mysql_conn(dbname, uname, pwd, hostname, portno):
    try:
        cnx = mysql_connector.connect(host=hostname, database=dbname, user=uname, password=pwd, port=portno)
        if cnx.is_connected:
            return {"connected": True}
    except mysql_connector.Error as err:
        return {"connected": False, "error": err}
