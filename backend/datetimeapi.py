import flask
from flask import jsonify
from flask import request
from flask_cors import CORS

from mainsql import create_connection
from mainsql import execute_read_query
from mainsql import execute_query

import maincreds

# Setting up an application name
app = flask.Flask(__name__)
# Allow to show errors in browser
app.config["DEBUG"] = True

CORS(app)


# Default url without any routing as GET request
@app.route('/', methods=['GET'])
def home():
    return "<h1> James Andersen Law Firm</h1>"


# Get all date time
@app.route('/api/date_time', methods=['GET'])
def api_datetime_all():

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "select * from date_time"
    datetime = execute_read_query(conn, sql)
    return jsonify(datetime)


# Add a date time appointment as POST method
@app.route('/api/date_time', methods=['POST'])
def api_add_datetime():

    request_data = request.get_json()
    new_date = request_data['Date']
    new_time = request_data['Time']
    new_availability = request_data['Availability']
    

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "insert into date_time (Date, Time, Availability) values ('%s','%s','%s')" % (new_date, new_time, new_availability)

    execute_query(conn, sql)
    return "Add new date time appointment successfully !"


# Update a date time as PUT method
@app.route('/api/date_time', methods=['PUT'])
def api_update_datetime():

    request_data = request.get_json()
    update_id = request_data['id']
    update_date = request_data['Date']
    update_time = request_data['Time']
    update_availability = request_data['Availability']
    

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "update date_time set date = '%s', time = '%s', availability = '%s' where id = %s" % (update_date, update_time, update_availability, update_id)

    execute_query(conn, sql)
    return f"DateTime with DateTime ID {update_id} updated successfully !"


# Delete a a date time with DELETE method
@app.route('/api/date_time', methods=['DELETE'])
def api_delete_datetime_byID():
    

    request_data = request.get_json()
    id_to_delete = request_data['id']
    
    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "delete from date_time where id = '%s'" % (id_to_delete)
    execute_query(conn, sql)
        
    return "Delete request successfully !"

app.run()





