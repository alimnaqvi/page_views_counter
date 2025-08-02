# import sqlite3
# import argparse
import psycopg2
import sys
import os
from dotenv import load_dotenv

if len(sys.argv) > 1:
    CONN_STRING = sys.argv[1]
else:
    print("No argument provided. Looking for environment variable named 'DATABASE_URL'")
    load_dotenv()
    try:
        CONN_STRING = os.environ["DATABASE_URL"]
    except Exception as e:
        print(f"Error retrieving environment variable: {e}")
        print("Please provide the connection string for PostgreSQL database, "
              "either as an argument to this script, or as an environment variable (.env will work)",
              "Example=\"postgresql://[user]:[password]@[neon_hostname]/[dbname]?sslmode=require&channel_binding=require\"",
              sep="\n")
        exit(1)

# parser = argparse.ArgumentParser(description="Show 10 entries from each table in a PostgreSQL database.")
# parser.add_argument(
#     "conn_string", help="Connection string for PostgreSQL database.\n\
#     Format=\"postgresql://[user]:[password]@[neon_hostname]/[dbname]?sslmode=require&channel_binding=require\"",
#     required=False
# )

# args = parser.parse_args()
# CONN_STRING = args.conn_string

try:
    with psycopg2.connect(CONN_STRING) as conn:
        print("Successfully connected to database")

        with conn.cursor() as cursor:
            # List tables
            print("Tables:")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            tables = cursor.fetchall()
            for table in tables:
                print(f"  {table[0]}")

            # Show first few rows of each table
            for table in tables:
                table_name = table[0]
                print(f"\n{table_name}:")
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
                rows = cursor.fetchall()
                for row in rows:
                    print(f"  {row}")

except Exception as e:
    print(f"Error connecting to database: {e}")
    exit(1)

# conn = sqlite3.connect(CONN_STRING)
# cursor = conn.cursor()

# # List tables
# print("Tables:")
# for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'"):
#     print(f"  {table[0]}")

# # Show first few rows of each table
# for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'"):
#     print(f"\n{table[0]}:")
#     for row in cursor.execute(f"SELECT * FROM {table[0]} LIMIT 10"):
#         print(f"  {row}")

# conn.close()
