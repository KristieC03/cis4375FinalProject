from flask import Flask, request, jsonify, session, make_response
from flask_cors import CORS, cross_origin
from datetime import datetime
import hashlib

from mainsql import create_connection
from mainsql import execute_read_query
from mainsql import execute_query

import maincreds



# ---- Start flask app ----
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"], methods=["GET", "OPTIONS"])
app.secret_key = 'supersecretkey'




# ---- LOGIN API (Basic Auth with SHA-256) ----
masterPassword = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # 'password'
masterUsername = 'username'

@app.route('/authenticatedroute', methods=['GET', 'OPTIONS'])
@cross_origin(origins="*", supports_credentials=True)
def auth_test():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    if request.authorization:
        encoded = request.authorization.password.encode()
        hasedResult = hashlib.sha256(encoded)
        if request.authorization.username == masterUsername and hasedResult.hexdigest() == masterPassword:
            return '<h1> Authorized user access </h1>'
    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})




# ---- CLIENT API ----
# Get all clients
@app.route('/api/clients', methods=['GET'])
def api_clients_all():

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "select * from clients"
    clients = execute_read_query(conn, sql)
    return jsonify(clients)


# Add a client as POST method
@app.route('/api/clients', methods=['POST'])
def api_add_client():

    request_data = request.get_json()
    new_fname = request_data['Client_Fname']
    new_lname = request_data['Client_Lname']
    new_email = request_data['Client_Email']
    new_phone = request_data['Client_Phone']
    # new_date = request_data['Client_Date']
    # new_time = request_data['Client_Time']

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "insert into clients (Client_Fname, Client_Lname, Client_Email, Client_Phone) values ('%s','%s','%s','%s')" % (new_fname, new_lname, new_email, new_phone)

    execute_query(conn, sql)
    return "Add new client successfully !"


# Update a client as PUT method
@app.route('/api/clients', methods=['PUT'])
def api_update_client():

    request_data = request.get_json()
    update_id = request_data['id']
    new_fname = request_data['Client_Fname']
    new_lname = request_data['Client_Lname']
    new_email = request_data['Client_Email']
    new_phone = request_data['Client_Phone']
    # new_date = request_data['Client_Date']
    # new_time = request_data['Client_Time']

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "update clients set Client_Fname = '%s', Client_Lname = '%s', Client_Email = '%s', Client_Phone = '%s' where id = %s" % (new_fname, new_lname, new_email, new_phone, update_id)

    execute_query(conn, sql)
    return f"Client with Client ID {update_id} updated successfully !"


# Delete a client with DELETE method
@app.route('/api/clients', methods=['DELETE'])
def api_delete_client_byID():
    

    request_data = request.get_json()
    id_to_delete = request_data['id']
    
    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "delete from clients where id = '%s'" % (id_to_delete)
    execute_query(conn, sql)
        
    return "Delete clients request successfully !"




# ---- BOOKING API ----
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
    new_datetime = request_data['Booking_Date']
    new_service = request_data['Booking_Service']
    new_status = request_data['Booking_Status']

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "insert into booking (Booking_Date, Booking_Service, Booking_Status) values ('%s','%s', '%s')" % (new_datetime, new_service, new_status)

    execute_query(conn, sql)
    return "Add new booking successfully !"





# Search appointments by first name, last name or both
@app.route('/api/search_bookings', methods=['GET'])
def search_bookings():

    first_name = request.args.get('first_name', '')
    last_name = request.args.get('last_name', '')
    
    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM booking JOIN clients ON booking.client_id = clients.client_id WHERE clients.client_fname LIKE %s OR clients.client_lname LIKE %s", (f'%{first_name}%', f'%{last_name}%'))

    bookings = cursor.fetchall()
    
    return jsonify(bookings), 200


# Search by start and end date
@app.route('/api/search_by_date', methods=['GET'])
def search_by_date():

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM booking WHERE booking_date BETWEEN %s AND %s", (start_date, end_date))
    bookings = cursor.fetchall()
    
    return jsonify(bookings), 200



# Guest view: Update availability of dates based on approval
@app.route('/api/update_availability', methods=['POST'])
def update_availability():

    approved_date = request.json['approved_date']
    
    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    cursor = conn.cursor()
    cursor.execute("UPDATE booking SET status = 'unavailable' WHERE booking_date = %s AND booking_status = 'approved'", (approved_date,))
    conn.commit()
    
    return jsonify({"message": "Availability updated"}), 200



# Auto delete if denied appointment
@app.route('/api/delete_denied_appointments', methods=['POST'])
def delete_denied_appointments():

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "DELETE FROM booking WHERE status = 'denied'"


    execute_query(conn, sql)
    return jsonify({"message": "Denied appointments deleted"}), 200


# Auto delete everything after 30 days
@app.route('/api/delete_old_appointments', methods=['POST'])
def delete_old_appointments():
    
    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM booking WHERE booking_date < NOW() - INTERVAL 30 DAY")
    conn.commit()
    
    return jsonify({"message": "Old appointments deleted"}), 200





# Update a booking as PUT method
@app.route('/api/booking', methods=['PUT'])
def api_update_booking():

    request_data = request.get_json()
    update_id = request_data['id']
    update_datetime = request_data['Booking_Date']
    update_service = request_data['Booking_Service']
    update_status = request_data['Booking_Status']
    

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "update booking set Booking_Date = '%s', Booking_Service = '%s', Booking_Status = '%s' where id = %s" % (update_datetime, update_service, update_status, update_id)

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






# ---- Run application ----
if __name__ == '__main__':
    app.run(debug=True, port=5050)

