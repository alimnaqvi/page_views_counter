# import sqlite3
from dotenv import load_dotenv
import os
import psycopg2

load_dotenv()

try:
    # DB_PATH = os.environ["DB_PATH"]
    CONN_STRING = os.environ["DATABASE_URL"]
except Exception as e:
    print(f"Error getting variable from the environment: {e}.")
    exit(1)

try:
    with psycopg2.connect(CONN_STRING) as conn:
        print("Connection with database established.")

        # Open a cursor to perform database operations
        with conn.cursor() as cursor:
            # Create a table to store view data
            # Using TEXT for timestamp to store in ISO 8601 format.
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS page_views (
                    id SERIAL PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    user_agent TEXT,
                    ip_address TEXT
                )
            ''')
            print("Finished creating table (if it didn't exist).")

            # Commit the changes to the database
            conn.commit()

except Exception as e:
    print(f"Error connecting to database: {e}.")
    exit(1)

# # Connect to the database (it will be created if it doesn't exist)
# conn = sqlite3.connect(DB_PATH)
# cursor = conn.cursor()

# # Create a table to store view data
# # Using TEXT for timestamp to store in ISO 8601 format.
# cursor.execute('''
#     CREATE TABLE IF NOT EXISTS page_views (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         timestamp TEXT NOT NULL,
#         user_agent TEXT,
#         ip_address TEXT
#     )
# ''')

# print(f"Database '{DB_PATH}' and table 'page_views' created successfully.")

# conn.commit()
# conn.close()
