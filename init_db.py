from dotenv import load_dotenv
import os
import psycopg2
import argparse

parser = argparse.ArgumentParser(
    description="Creates a PostgreSQL table (URL taken from .env) if it did not exist."
    "Does not modify the table if it existed, unless --drop option is specified."
)

parser.add_argument("-d", "--drop", action="store_true", help="Drop/delete a table if it exists in the database.")

args = parser.parse_args()

load_dotenv()
try:
    CONN_STRING = os.environ["DATABASE_URL"]
except Exception as e:
    print(f"Error getting variable from the environment: {e}.")
    exit(1)

try:
    with psycopg2.connect(CONN_STRING) as conn:
        print("Connection with database established.")

        # Open a cursor to perform database operations
        with conn.cursor() as cursor:
            # Drop the table if it already exists and 'drop' argument is provided
            if args.drop:
                cursor.execute("DROP TABLE IF EXISTS page_views;")
                print("Dropped table page_views (if it existed).")

            # Create a table to store view data
            # Using TEXT for timestamp to store in ISO 8601 format.
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS page_views (
                    id SERIAL PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    user_agent TEXT,
                    ip_address TEXT,
                    src TEXT,
                    src_uri TEXT
                );
            ''')
            print("Finished creating table (if it didn't exist).")

            # Add new columns if table already exists and doesn't have these columns.
            cursor.execute('''
                ALTER TABLE page_views
                ADD COLUMN IF NOT EXISTS src TEXT,
                ADD COLUMN IF NOT EXISTS src_uri TEXT;
            ''')
            print("Finished adding new columns (if they didn't exist).")

            # Commit the changes to the database
            conn.commit()

except Exception as e:
    print(f"Error connecting to database: {e}.")
    exit(1)
