from flask import Flask, request, jsonify, session, make_response
from flask_cors import CORS, cross_origin
from flask_apscheduler import APScheduler
from datetime import datetime
import bcrypt
import pytz

from mainsql import create_connection, execute_read_query, execute_query
from maincreds import Creds

# ---- Start flask app ----
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "OPTIONS"])
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

@app.route('/api/book-appointment', methods=['POST'])
def create_booking():
    data = request.get_json()

    first_name = data.get('firstName')
    last_name = data.get('lastName')
    email = data.get('email')
    phone = data.get('phone')
    service = data.get('serviceType')
    notes = data.get('notes')
    booking_datetime_iso = data.get('booking_datetime')  # ISO string sent from frontend

    try:
        # Convert ISO string to datetime object (make sure timezone is handled)
        booking_datetime_obj = datetime.fromisoformat(booking_datetime_iso.replace("Z", "+00:00"))

        # Format it to store in MySQL as 'YYYY-MM-DD HH:MM:SS'
        booking_datetime = booking_datetime_obj.strftime('%Y-%m-%d %H:%M:%S')

        myCreds = Creds()
        conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
        cursor = conn.cursor()

        # Insert into Clients table
        insert_client_sql = """
            INSERT INTO Clients (Client_FName, Client_LName, Client_Email, Client_Phone)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_client_sql, (first_name, last_name, email, phone))
        client_id = cursor.lastrowid

        # Insert into Booking table, including Booking_Submitted
        insert_booking_sql = """
            INSERT INTO Booking (Client_ID, Booking_Date, Booking_Service, Booking_Status, Booking_Notes, Booking_Submitted)
            VALUES (%s, %s, %s, %s, %s, NOW())  -- 'NOW()' inserts the current timestamp
        """
        cursor.execute(insert_booking_sql, (client_id, booking_datetime, service, 'pending', notes))
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Booking request submitted successfully!"
        }), 201

    except Exception as e:
        print("❌ Error in booking:", e)
        return jsonify({
            "success": False,
            "message": "Failed to create booking.",
            "error": str(e)
        }), 500



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
    b.Booking_Date AS booking_datetime,
    b.Booking_Service AS serviceType,
    b.Booking_Status AS status,
    b.Booking_Notes AS notes
    FROM Booking b
    JOIN Clients c ON b.Client_ID = c.Client_ID;
    """
    raw_bookings = execute_read_query(conn, sql)

    bookings = []
    approved_dates = []

    # Define timezone
    utc = pytz.utc
    local_tz = pytz.timezone('America/Chicago')

    for b in raw_bookings:
        dt_utc = b['booking_datetime']
        dt_local = utc.localize(dt_utc).astimezone(local_tz)

        # Format for display
        formatted_date = dt_local.strftime('%B %d, %Y')  # Example: April 14, 2025
        formatted_time = dt_local.strftime('%I:%M %p')   # Example: 03:00 PM

        # Format for FullCalendar (ISO 8601)
        iso_datetime = dt_local.strftime('%Y-%m-%dT%H:%M:%S')

        # Format phone number (###) ###-####
        raw_phone = b['phone']
        formatted_phone = f"({raw_phone[:3]}) {raw_phone[3:6]}-{raw_phone[6:]}" if raw_phone and len(raw_phone) == 10 else raw_phone

        bookings.append({
            "firstName": b['firstName'],
            "lastName": b['lastName'],
            "email": b['email'],
            "phone": formatted_phone,
            "date": formatted_date,
            "time": formatted_time,
            "dateTimeISO": iso_datetime,
            "serviceType": b['serviceType'],
            "status": b['status'],
            "notes": b['notes']
        })

        if b['status'] == 'approved':
            approved_dates.append(iso_datetime)

    return jsonify({
        "bookings": bookings,
        "approved_dates": approved_dates
    })



from datetime import datetime
import pytz

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


@app.route('/api/approved-bookings', methods=['GET'])
def get_approved_bookings():
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)

    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    sql = """
        SELECT Booking_Date 
        FROM Booking 
        WHERE Booking_Status = 'approved';
    """

    results = execute_read_query(conn, sql)

    # Convert Booking_Date to ISO format for easier frontend handling
    formatted_results = [row['Booking_Date'].isoformat() for row in results if row['Booking_Date']]

    return jsonify(formatted_results)




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
