from mysql import connector as mysql_connector


def check_db_connection(dbtype, db_name, username, password, portno, **kwargs):
    print("Came in check_db_connection with portno as :", type(portno))
    hostname = kwargs["hostname"]
    if dbtype == "postgres":
        check_pgsql(db_name, username, password, **kwargs)
    if dbtype.lower() == "mysql":
        connection_status = check_mysql_conn(db_name, username, password, hostname, portno)
        print("fromcheck_db_connetion:", connection_status)
        return connection_status


def check_pgsql(db_name, username, password, **kwargs):
    pass


def check_mysql_conn(db_name, uname, pwd, hostname, portno):
    try:
        cnx = mysql_connector.connect(host=hostname, database=db_name, user=uname, password=pwd, port=portno)
        if cnx.is_connected:
            return {"connected": True}
    except mysql_connector.Error as err:
        print(f"Error#{err.errno}, msg: {err.msg}")
        return {"connected": False, "error": err}

