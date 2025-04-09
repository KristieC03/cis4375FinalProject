from flask import Flask, request, jsonify, session, make_response
from flask_cors import CORS, cross_origin
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
        b.Booking_Date AS date,
        b.Booking_Service AS serviceType,
        b.Booking_Status AS status,
        b.Booking_Notes AS notes
    FROM Booking b
    JOIN Clients c ON b.Client_ID = c.Client_ID;
    """
    bookings = execute_read_query(conn, sql)
    return jsonify(bookings)

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

@app.route('/api/search_bookings', methods=['GET'])
def search_bookings():
    fname = request.args.get('first_name', '')
    lname = request.args.get('last_name', '')
    sql = """
        SELECT * FROM Booking
        JOIN Clients ON Booking.Client_ID = Clients.Client_ID
        WHERE Clients.Client_FName LIKE %s OR Clients.Client_LName LIKE %s
    """
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, (f'%{fname}%', f'%{lname}%'))
    return jsonify(cursor.fetchall()), 200

@app.route('/api/search_by_date', methods=['GET'])
def search_by_date():
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    sql = "SELECT * FROM Booking WHERE Booking_Date BETWEEN %s AND %s"
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, (start, end))
    return jsonify(cursor.fetchall()), 200

@app.route('/api/update_availability', methods=['POST'])
def update_availability():
    approved_date = request.json['approved_date']
    sql = "UPDATE Booking SET Booking_Status = 'unavailable' WHERE Booking_Date = %s AND Booking_Status = 'approved'"
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    cursor = conn.cursor()
    cursor.execute(sql, (approved_date,))
    conn.commit()
    return jsonify({"message": "Availability updated"}), 200

@app.route('/api/delete_denied_appointments', methods=['POST'])
def delete_denied_appointments():
    sql = "DELETE FROM Booking WHERE Booking_Status = 'denied'"
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    execute_query(conn, sql)
    return jsonify({"message": "Denied appointments deleted"}), 200

@app.route('/api/delete_old_appointments', methods=['POST'])
def delete_old_appointments():
    sql = "DELETE FROM Booking WHERE Booking_Date < NOW() - INTERVAL 30 DAY"
    myCreds = Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    return jsonify({"message": "Old appointments deleted"}), 200

# ---- Run app ----
if __name__ == '__main__':
    app.run(debug=True, port=5050)
