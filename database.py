import logging
import re
import sqlite3

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

database = 'heimdall.sqlite'


def create_connection():
    """Create a connection to the SQLite database."""
    connector = sqlite3.connect(database)
    return connector


def fetch_column_names(connection, table_name, include_primary=False):
    cursor = connection.cursor()

    # Query to fetch column names from the specified table
    query = f"PRAGMA table_info({table_name})"
    cursor.execute(query)

    # Fetch all rows from the result set
    columns = cursor.fetchall()

    # Extract column names from the result set
    column_names = [column[1] for column in columns]
    if not include_primary:
        column_names = column_names[1:]
    return column_names


def insert_data(connection, table_name, data):
    columns = fetch_column_names(connection, table_name)
    # Convert the list of column names to a comma-separated string
    columns_str = ', '.join(columns)
    """Insert data into the specified table."""
    cursor = connection.cursor()
    placeholders = ', '.join(['?'] * len(data))
    insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    cursor.execute(insert_query, data)
    last_inserted_id = cursor.lastrowid
    connection.commit()
    return last_inserted_id


def execute_query(connection, query):
    """Execute a custom SQL query."""
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()


def fetch_data(connection, query):
    """Fetch data from the SQLite database."""
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()

    # Fetch column names directly from the cursor
    columns = [column[0] for column in cursor.description]

    final_result = [dict(zip(columns, item)) for item in result]
    return final_result


def extract_table_name(sql_query):
    # Assuming a simple SELECT statement for demonstration purposes
    match = re.search(r'FROM\s+([^\s;]+)', sql_query, re.IGNORECASE)

    if match:
        return match.group(1)
    else:
        return None


def close_connection(connection):
    """Close the SQLite database connection."""
    connection.close()
