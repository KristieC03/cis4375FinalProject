from flask import Flask, request, jsonify, session, make_response
from flask_cors import CORS, cross_origin
from flask_apscheduler import APScheduler
from datetime import datetime
import bcrypt

from mainsql import create_connection, execute_read_query, execute_query
from maincreds import Creds

# ---- Start flask app ----
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"], methods=["GET", "OPTIONS"])
app.secret_key = 'supersecretkey'

# ---- LOGIN API (Basic Auth with bycrypt) ----
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

    auth = request.authorization
    if not auth:
        return make_response('Could not verify', 401, {
            'WWW-Authenticate': 'Basic realm="Login Required"'
        })

    username = auth.username
    input_password = auth.password.encode()  # raw bytes

    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    cursor = conn.cursor(dictionary=True)

    # Get hashed password from DB
    query = "SELECT Admin_Password FROM Admins WHERE Admin_Username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()

    if result:
        stored_hash = result['Admin_Password'].encode()  # bcrypt hash
        if bcrypt.checkpw(input_password, stored_hash):
            return '<h1>Authorized user access</h1>'

    return make_response('Could not verify', 401, {
        'WWW-Authenticate': 'Basic realm="Login Required"'
    })
# ---- CLIENT API ----
''' Don't rlly need, commented out for now just in case, might delete later
@app.route('/api/clients', methods=['GET'])
def api_clients_all():
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "SELECT * FROM clients"
    clients = execute_read_query(conn, sql)
    return jsonify(clients)

@app.route('/api/clients', methods=['POST'])
def api_add_client():
    data = request.get_json()
    sql = f"""
        INSERT INTO clients (Client_Fname, Client_Lname, Client_Email, Client_Phone)
        VALUES ('{data['Client_Fname']}', '{data['Client_Lname']}', '{data['Client_Email']}', '{data['Client_Phone']}')
    """
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    execute_query(conn, sql)
    return "Add new client successfully!"

@app.route('/api/clients', methods=['PUT'])
def api_update_client():
    data = request.get_json()
    sql = f"""
        UPDATE clients SET Client_Fname = '{data['Client_Fname']}', Client_Lname = '{data['Client_Lname']}',
        Client_Email = '{data['Client_Email']}', Client_Phone = '{data['Client_Phone']}' WHERE id = {data['id']}
    """
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    execute_query(conn, sql)
    return f"Client with Client ID {data['id']} updated successfully!"

@app.route('/api/clients', methods=['DELETE'])
def api_delete_client_byID():
    id_to_delete = request.get_json()['id']
    sql = f"DELETE FROM clients WHERE id = '{id_to_delete}'"
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    execute_query(conn, sql)
    return "Delete clients request successfully!"
'''

# ---- BOOKING API ----
@app.route('/api/booking', methods=['GET'])
def api_bookings_all():
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)

    sql = """
    SELECT 
    c.Client_FName AS firstName,
    c.Client_LName AS lastName,
    c.Client_Email AS email,
    c.Client_Phone AS phone,
    DATE_FORMAT(b.Booking_Date, '%Y-%m-%d') AS date,
    TIME_FORMAT(b.Booking_Date, '%h:%i %p') AS time,
    b.Booking_Service AS serviceType,
    b.Booking_Status AS status,
    b.Booking_Notes AS notes
FROM Booking b
JOIN Clients c ON b.Client_ID = c.Client_ID;
"""
    bookings = execute_read_query(conn, sql)
    # Filter out the approved bookings' dates
    approved_dates = [booking['date'] for booking in bookings if booking['status'] == 'approved']
    return jsonify({
        "bookings": bookings,
        "approved_dates": approved_dates  # Sending approved booking dates to the frontend
    })

@app.route('/api/booking-requests', methods=['GET'])
def get_pending_bookings():
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    sql = """
        SELECT 
            b.Booking_ID,
            c.Client_ID,
            c.Client_FName AS firstName,
            c.Client_LName AS lastName,
            c.Client_Email AS email,
            c.Client_Phone AS phone,
            b.Booking_Date AS date,
            b.Booking_Service AS serviceType,
            b.Booking_Status AS status,
            b.Booking_Notes AS notes
        FROM Booking b
        JOIN Clients c ON b.Client_ID = c.Client_ID
        WHERE b.Booking_Status = 'pending';
    """
    results = execute_read_query(conn, sql)
    return jsonify(results)

# ---- APPROVE A BOOKING ----
@app.route('/api/booking-requests/approve/<booking_id>', methods=['POST'])
def approve_booking(booking_id):
    sql = f"""
        UPDATE Booking
        SET Booking_Status = 'approved'
        WHERE Booking_ID = {booking_id}
    """
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)

    try:
        print(f"Approving booking: {booking_id}")
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()

        print("Query executed. Rows affected:", cursor.rowcount)

        if cursor.rowcount == 0:
            # Verify it even exists at all
            check_sql = f"SELECT * FROM Booking WHERE Booking_ID = {booking_id}"
            found = execute_read_query(conn, check_sql)
            if found:
                return jsonify({"success": False, "message": "Booking found but not updated"}), 500
            return jsonify({"success": False, "message": f"No booking with ID {booking_id}"}), 404

        return jsonify({
            "success": True,
            "message": f"Booking {booking_id} approved"
        }), 200

    except Exception as e:
        print("Approve Error:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# ---- DENY A BOOKING ----
@app.route('/api/booking-requests/delete/<int:booking_id>', methods=['DELETE'])
def delete_booking_and_client(booking_id):
    try:
        myCreds = Creds()
        connection = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
        cursor = connection.cursor(dictionary=True)

        # Get the Client_ID before deleting the booking
        cursor.execute("SELECT Client_ID FROM Booking WHERE Booking_ID = %s", (booking_id,))
        booking = cursor.fetchone()

        if not booking:
            return jsonify({'success': False, 'error': f'Booking ID {booking_id} not found'}), 404

        client_id = booking['Client_ID']

        # Delete the booking
        cursor.execute("DELETE FROM Booking WHERE Booking_ID = %s", (booking_id,))
        connection.commit()

        # Delete the associated client
        cursor.execute("DELETE FROM Clients WHERE Client_ID = %s", (client_id,))
        connection.commit()

        return jsonify({'success': True, 'message': f'Booking {booking_id} and Client {client_id} deleted'})

    except Exception as e:
        print(f"❌ Error deleting booking/client: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/booking', methods=['PUT'])
def api_update_booking():
    data = request.get_json()
    sql = f"""
        UPDATE Booking
        SET Booking_Date = '{data['Booking_Date']}', Booking_Service = '{data['Booking_Service']}',
        Booking_Status = '{data['Booking_Status']}'
        WHERE Booking_ID = {data['id']}
    """
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    execute_query(conn, sql)
    return f"Booking with Booking ID {data['id']} updated successfully!"

@app.route('/api/booking', methods=['DELETE'])
def api_delete_booking_byID():
    id_to_delete = request.get_json()['id']
    sql = f"DELETE FROM Booking WHERE Booking_ID = {id_to_delete}"
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    execute_query(conn, sql)
    return "Delete booking request successfully!"

class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

def delete_old_appointments_job():
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    cursor = conn.cursor(dictionary=True)

    # Step 1: Select all bookings older than 30 days
    select_sql = """
        SELECT b.Booking_ID, b.Booking_Date, b.Booking_Service,
               c.Client_ID, c.Client_FName, c.Client_LName
        FROM Booking b
        JOIN Clients c ON b.Client_ID = c.Client_ID
        WHERE b.Booking_Date < NOW() - INTERVAL 30 DAY
    """
    cursor.execute(select_sql)
    old_bookings = cursor.fetchall()

    if not old_bookings:
        print(f"{datetime.now()}: No old appointments to delete.")
        return

    # Step 2: Log each one
    for booking in old_bookings:
        print(f"{datetime.now()}: Deleting booking ID {booking['Booking_ID']} for {booking['Client_FName']} {booking['Client_LName']} ({booking['Booking_Service']} on {booking['Booking_Date']})")

    # Step 3: Delete from Booking table
    booking_ids = [str(b['Booking_ID']) for b in old_bookings]
    delete_bookings_sql = f"DELETE FROM Booking WHERE Booking_ID IN ({','.join(booking_ids)})"
    cursor.execute(delete_bookings_sql)
    conn.commit()

    # Step 4: Delete the associated clients
    client_ids = [str(b['Client_ID']) for b in old_bookings]
    delete_clients_sql = f"DELETE FROM Clients WHERE Client_ID IN ({','.join(client_ids)})"
    cursor.execute(delete_clients_sql)
    conn.commit()

    print(f"{datetime.now()}: Deleted {len(old_bookings)} old appointment(s) and associated client(s).")

scheduler.add_job(
    id='Delete Old Appointments',
    func=delete_old_appointments_job,
    trigger='interval',
    days=1
)

if __name__ == '__main__':
    app.run(debug=True, port=5050, use_reloader=False)

