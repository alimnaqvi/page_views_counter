# This script adds to Postgres database the entries (GET requests) that have been missed due to a server/deployment error
# The required details are read from log entries JSON file (e.g., Google Cloud Run logs)

import json
from pathlib import Path
# from datetime import datetime
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import os
import psycopg2

LOG_JSON_PATH = Path("./cloud_run_logs/downloaded-logs-20250926-183912.json")

load_dotenv()
try:
    CONN_STRING = os.environ["DATABASE_URL"]
except Exception as e:
    print(f"Error getting variable from the environment: {e}.")
    exit(1)

def main():
    # Check for file existence
    if not LOG_JSON_PATH.exists:
        print("JSON log file does not exist:", LOG_JSON_PATH)
        exit(1)

    # counter variables for observability
    json_item_count = 0
    added_to_db_count = 0
    
    try:
        # Connect to database
        with psycopg2.connect(CONN_STRING) as conn:
            print("Connection with database established.")

            # Open a cursor to perform database operations
            with conn.cursor() as cursor:

                # Open file for reading
                with open(LOG_JSON_PATH, "r") as json_file:
                    print("JSON file successfully opened for reading.")
                    # Read the file contents as a json object
                    json_contents = json.load(json_file)

                    # Loop through items in the json file
                    for json_item in json_contents:
                        json_item_count += 1

                        # Get the timestamp of the request
                        timestamp = json_item["timestamp"].replace('Z', '+00:00')

                        # Start processing the GET requests
                        requestMethod = json_item["httpRequest"]["requestMethod"]
                        if json_item["httpRequest"]["requestMethod"] == "GET":
                            # Get user-agent
                            user_agent = json_item["httpRequest"]["userAgent"]
                            # get IP address
                            ip_address = json_item["httpRequest"]["remoteIp"]
                            # Get query parameters
                            parsed_url = urlparse(json_item["httpRequest"]["requestUrl"])
                            parsed_queries = parse_qs(parsed_url.query)
                            src = parsed_queries.get("src", [""])[0]
                            src_uri = parsed_queries.get("src_uri", [""])[0]

                            # Update database with new value
                            cursor.execute(
                                "INSERT INTO page_views (timestamp, user_agent, ip_address, src, src_uri) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                                (timestamp, user_agent, ip_address, src, src_uri)
                            )
                            conn.commit()

                            added_to_db_count += 1

                        else:
                            print(f"Skipping non-GET request: {requestMethod}")

    except Exception as e:
        print(f"An exception occured: {e}")
        exit(1)
    
    print(f"Successully added {added_to_db_count} rows after processing {json_item_count} items in the json log file")


if __name__ == "__main__":
    main()