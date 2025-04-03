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


# Get all bookings
@app.route('/api/booking', methods=['GET'])
def api_bookings_all():

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "select * from booking"
    bookings = execute_read_query(conn, sql)
    return jsonify(bookings)


# Add a booking as POST method
@app.route('/api/booking', methods=['POST'])
def api_add_booking():

    request_data = request.get_json()
    new_client = request_data['Client_ID']
    new_datetime = request_data['Date_Time_ID']
    new_status = request_data['Booking_Status']
    new_approval = request_data['Booking_Approval']
    new_detail = request_data['Booking_Details']

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "insert into booking (Client_ID, Date_Time_ID, Booking_Status, Booking_Approval, Booking_Details) values ('%s','%s','%s', '%s', '%s')" % (new_client, new_datetime, new_status, new_approval, new_detail)

    execute_query(conn, sql)
    return "Add new booking successfully !"


# Update a booking as PUT method
@app.route('/api/booking', methods=['PUT'])
def api_update_booking():

    request_data = request.get_json()
    update_id = request_data['id']
    update_client = request_data['Client_ID']
    update_datetime = request_data['Date_Time_ID']
    update_status = request_data['Booking_Status']
    update_approval = request_data['Booking_Approval']
    update_detail = request_data['Booking_Details']

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "update booking set Client_ID = '%s', Date_Time_ID = '%s', Booking_Status = '%s', Booking_Approval = '%s', Booking_Details = '%s' where id = %s" % (update_client, update_datetime, update_status, update_approval, update_detail, update_id)

    execute_query(conn, sql)
    return f"Booking with Booking ID {update_id} updated successfully !"


# Delete a booking with DELETE method
@app.route('/api/booking', methods=['DELETE'])
def api_delete_booking_byID():
    

    request_data = request.get_json()
    id_to_delete = request_data['id']
    
    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "delete from booking where id = '%s'" % (id_to_delete)
    execute_query(conn, sql)
        
    return "Delete booking request successfully !"

app.run()




