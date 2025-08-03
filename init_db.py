from dotenv import load_dotenv
import os
import psycopg2
import sys

if len(sys.argv) > 1:
    if sys.argv[1] == "drop":
        DROP_TABLE = True
    else:
        print(f"Unknown argument: {sys.argv[1]}", "The only allowed argument is 'drop'", file=sys.stderr, sep='\n')
        exit(1)
else:
    DROP_TABLE = False

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
            if DROP_TABLE:
                cursor.execute("DROP TABLE IF EXISTS page_views;")
                print("Dropped table page_views (if it existed).")

            # Create a table to store view data
            # Using TEXT for timestamp to store in ISO 8601 format.
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS page_views (
                    id SERIAL PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    user_agent TEXT,
                    ip_address TEXT
                );
            ''')
            print("Finished creating table (if it didn't exist).")

            # Commit the changes to the database
            conn.commit()

except Exception as e:
    print(f"Error connecting to database: {e}.")
    exit(1)
