import base64
import os

from flask import Flask, jsonify, request, send_from_directory
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


@app.route('/images/<directory>/<filename>')
def serve_image(directory, filename):
    return send_from_directory(directory, filename)


@app.route('/api/settings', methods=['GET'])
def get_settings():
    conn = database.create_connection()

    # Fetch data
    items = database.fetch_data(conn, "SELECT * FROM 'settings' order by group_id asc")
    groups = database.fetch_data(conn, "SELECT * FROM 'setting_groups' order by `order` asc")
    user_config_list = database.fetch_data(conn, "SELECT * FROM 'setting_user' where user_id=2 order by setting_id asc")
    user_config = {}
    for group in groups:
        group['title'] = create_text_using_translation_key(group['title'])

    for value in user_config_list:
        user_config[value["setting_id"]] = value["uservalue"]

    for item in items:
        item['label'] = create_text_using_translation_key(item['label'])
        if item['id'] in user_config:
            value = user_config[item['id']]
            item['user_value'] = value if not is_image(value) else create_absolute_path(value)
        else:
            item['user_value'] = ""
    database.close_connection(conn)
    return jsonify({'config_items': items, 'config_groups': groups})


@app.route('/api/applications', methods=['GET'])
def get_applications():
    conn = database.create_connection()

    # Fetch data
    items = database.fetch_data(conn, "SELECT * FROM 'items' where user_id=2 and type=0 order by title")
    for item in items:
        if item['icon']:
            item['icon'] = create_absolute_path(item['icon'])
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
    for user in users:
        if user["avatar"]:
            user['avatar'] = create_absolute_path(user['avatar'])
    database.close_connection(conn)
    return jsonify({'users': users})


def is_image(filename):
    if filename.endswith(".jpg") or filename.endswith(".png") or filename.endswith(".jpeg") or filename.endswith(
            ".svg"):
        return True
    else:
        return False


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        # Encode the image file content to Base64
        base64_string = base64.b64encode(image_file.read()).decode('utf-8')
        return base64_string


def create_absolute_path(image_path):
    return f"http://localhost:{port}/images/" + image_path


def create_text_using_translation_key(trans_key):
    return str(trans_key.rsplit('.', 1)[-1]).replace("_", " ").title()


if __name__ == '__main__':
    # app.run(debug=True, port=port)
    serve(app, host="0.0.0.0", port=port)
