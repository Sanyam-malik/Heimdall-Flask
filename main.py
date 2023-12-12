import os
from flask import Flask, jsonify, request
from flask_cors import CORS  # Import the CORS extension
import logging

from waitress import serve

import database

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

port = 5000
if "PORT" in os.environ:
    port = os.environ["PORT"]


@app.route('/', methods=['GET'])
def home():
    return "Heimdall-Flask is Active"


@app.route('/api/settings', methods=['GET'])
def get_settings():
    conn = database.create_connection()

    # Fetch data
    items = database.fetch_data(conn, "SELECT * FROM 'settings' order by group_id asc")
    groups = database.fetch_data(conn, "SELECT * FROM 'setting_groups' order by `order` asc")
    user_config_list = database.fetch_data(conn, "SELECT * FROM 'setting_user' where user_id=2 order by setting_id asc")
    user_config = {}
    for value in user_config_list:
        user_config[value["setting_id"]] = value["uservalue"]

    for item in items:
        if item['id'] in user_config:
            item['user_value'] = user_config[item['id']]
        else:
            item['user_value'] = ""
    database.close_connection(conn)
    return jsonify({'config_items': items, 'config_groups': groups})


@app.route('/api/applications', methods=['GET'])
def get_applications():
    conn = database.create_connection()

    # Fetch data
    items = database.fetch_data(conn, "SELECT * FROM 'items' where user_id=2 and type=0 order by title")
    database.close_connection(conn)
    return jsonify({'applications': items})


@app.route('/api/tags', methods=['GET'])
def get_tags():
    conn = database.create_connection()

    # Fetch data
    item_association = database.fetch_data(conn, "SELECT * FROM 'item_tag' order by item_id")
    tags = database.fetch_data(conn, "SELECT * FROM 'items' where user_id=2 and type=1 order by title")
    database.close_connection(conn)
    return jsonify({'tags_association': item_association, 'tags': tags})


@app.route('/api/users', methods=['GET'])
def get_users():
    conn = database.create_connection()

    # Fetch data
    users = database.fetch_data(conn, "SELECT * FROM 'users'")
    database.close_connection(conn)
    return jsonify({'users': users})


if __name__ == '__main__':
    # app.run(debug=True, port=port)
    serve(app, host="0.0.0.0", port=port)
