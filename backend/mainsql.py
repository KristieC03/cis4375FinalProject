import mysql.connector
from mysql.connector import Error

# This function is used to create a connection
def create_connection(hostname, uname, pwd, dbname):
    connection = None
    try:
        connection = mysql.connector.connect(
            host= hostname,
            user= uname,
            password= pwd,
            database= dbname
        )
        print('connection successful')
    except Error as e:
        print('connection unsuccessful, error is :', e)
    return connection

# This function is used to execute query to update database (insert, update and delete statement)
def execute_query(conn, query):
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        conn.commit()
        print('Query executed successfully')
    except Error as e:
        print('Error occured is: ', e)
# This function is used to execute query to retrive records from database (select statement)
def execute_read_query(conn, query):
    cursor = conn.cursor(dictionary = True)
    rows = None
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    except Error as e:
        print('Error occured is : ', e)

