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
def api_captains_all():

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "select * from clients"
    captains = execute_read_query(conn, sql)
    return jsonify(captains)


# Add a client as POST method
@app.route('/api/clients', methods=['POST'])
def api_add_client():

    request_data = request.get_json()
    new_fname = request_data['fname']
    new_lname = request_data['lname']
    new_email = request_data['email']
    new_phone = request_data['phone']

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "insert into clients (fname, lname, email, phone) values ('%s','%s','%s','%s')" % (new_fname, new_lname, new_email, new_phone)

    execute_query(conn, sql)
    return "Add new client successfully !"


# Update a client as PUT method
@app.route('/api/clients', methods=['PUT'])
def api_update_client():

    request_data = request.get_json()
    update_id = request_data['id']
    update_fname = request_data['fname']
    update_lname = request_data['lname']
    update_email = request_data['email']
    update_phone = request_data['phone']

    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "update captain set firstname = '%s', lastname = '%s', ranking = '%s', homeplanet = '%s' where id = %s" % (update_fname, update_lname, update_email, update_phone, update_id)

    execute_query(conn, sql)
    return f"Captain with Captain ID {update_id} updated successfully !"


# Delete a client with DELETE method
@app.route('/api/clients', methods=['DELETE'])
def api_delete_client_byID():
    

    request_data = request.get_json()
    id_to_delete = request_data['id']
    
    myCreds = maincreds.Creds()
    conn = create_connection(myCreds.connectionstring, myCreds.username, myCreds.passwd, myCreds.dataBase)
    sql = "delete from captain where id = '%s'" % (id_to_delete)
    execute_query(conn, sql)
        
    return "Delete captain request successfully !"

app.run()




