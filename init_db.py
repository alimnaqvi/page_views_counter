import sqlite3
from dotenv import load_dotenv
import os

load_dotenv()

try:
    DB_PATH = os.environ["DB_PATH"]
except Exception as e:
    print(f"Error getting variable from the environment: {e}.")
    exit(1)

# Path to the database
DB_PATH = 'views.db'

# Connect to the database (it will be created if it doesn't exist)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create a table to store view data
# Using TEXT for timestamp to store in ISO 8601 format.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS page_views (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        user_agent TEXT,
        ip_address TEXT
    )
''')

print(f"Database '{DB_PATH}' and table 'page_views' created successfully.")

conn.commit()
conn.close()
