import mysql.connector
from mysql.connector import Error

def create_connection(hostname, uname, pwd, dbname):
    """
    Establishes a connection to the MySQL database.
    """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=hostname,
            user=uname,
            password=pwd,
            database=dbname
        )
        print('Connection successful')
    except Error as e:
        print('Connection unsuccessful. Error:', e)
    return connection


def execute_query(conn, query, params=None):
    """
    Executes INSERT, UPDATE, DELETE queries.
    """
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        print('Query executed successfully')
    except Error as e:
        print('Error occurred:', e)
    finally:
        cursor.close()


def execute_read_query(conn, query, params=None):
    """
    Executes SELECT queries and returns the result as a list of dictionaries.
    """
    cursor = conn.cursor(dictionary=True)
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print('Error occurred:', e)
        return None
    finally:
        cursor.close()

