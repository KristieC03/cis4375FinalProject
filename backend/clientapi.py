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
    sql = "insert into clients (Client_Fname, Client_Lname, Client_Email, Client_Phone) values ('%s','%s','%s','%s','%s','%s')" % (new_fname, new_lname, new_email, new_phone)

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

app.run()




