import sqlite3
import argparse

parser = argparse.ArgumentParser(description="Show 10 entries from each table in a sqlite3 database.")
parser.add_argument("db_path", help="Path to sqlite3 database")
args = parser.parse_args()
DB_PATH = args.db_path

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# List tables
print("Tables:")
for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(f"  {table[0]}")

# Show first few rows of each table
for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(f"\n{table[0]}:")
    for row in cursor.execute(f"SELECT * FROM {table[0]} LIMIT 10"):
        print(f"  {row}")

conn.close()
