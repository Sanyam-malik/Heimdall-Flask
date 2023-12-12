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


@app.route('/api/tags/<tag_filter>', methods=['GET'])
def get_tags_filter(tag_filter=None):
    return generate_tags(tag_filter)


@app.route('/api/tags', methods=['GET'])
def get_tags():
    return generate_tags()


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


def generate_tags(tag_filter=None):
    conn = database.create_connection()
    filter_str = ""
    # Extract path variable
    if tag_filter:
        filter_str = "and `title` LIKE '%" + str(tag_filter).lower() + "%'"
    # Fetch data
    items = database.fetch_data(conn,
                                "SELECT * FROM 'items' i WHERE i.`user_id`=2 AND i.`type`=0 ORDER BY i.`order` ASC")
    for item in items:
        item['icon'] = create_absolute_path(item['icon']) if item['icon'] else None

    items = convert_list_to_dict(items, "id")
    item_association = convert_list_to_map(database.fetch_data(conn, "SELECT * FROM 'item_tag' ORDER BY item_id"),
                                           "tag_id")
    tags = database.fetch_data(conn, f"SELECT * FROM 'items' WHERE `type`=1 {filter_str} ORDER BY `title`")
    for tag in tags:
        tag['title'] = create_text_using_translation_key(tag['title'])
        item_list = [items[item['item_id']] for item in item_association.get(tag['id'], []) if
                     item['item_id'] in items] if item_association.get(tag['id']) else []
        if str(tag['title']).lower() == "dashboard":
            other_tags = database.fetch_data(conn, f"SELECT * FROM 'items' WHERE `type`=1 and id !=0 ORDER BY `order`")
            for other_tag in other_tags:
                item_list.append(other_tag)
        tag['items'] = sorted(item_list, key=lambda x: x['order'])
    database.close_connection(conn)
    return jsonify({'tags': tags})


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        # Encode the image file content to Base64
        base64_string = base64.b64encode(image_file.read()).decode('utf-8')
        return base64_string


def create_absolute_path(image_path):
    return f"http://localhost:{port}/images/" + image_path


def create_text_using_translation_key(trans_key):
    return str(trans_key.rsplit('.', 1)[-1]).replace("_", " ").title()


# Function to convert list of objects to map of lists based on a key
def convert_list_to_map(list_of_objects, key):
    result_map = {}
    for obj in list_of_objects:
        key_value = obj[key]
        if key_value not in result_map:
            result_map[key_value] = []
        result_map[key_value].append(obj)
    return result_map


# Function to convert list of dictionaries to dictionary of dictionaries based on a key
def convert_list_to_dict(list_of_dicts, key):
    return {obj[key]: obj for obj in list_of_dicts}


if __name__ == '__main__':
    # app.run(debug=True, port=port)
    serve(app, host="0.0.0.0", port=port, threads=100)
