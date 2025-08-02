# import sqlite3
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse

from dotenv import load_dotenv
import os
import sys
import psycopg2

load_dotenv()

# Path to the database and the log file
try:
    # DB_PATH = os.environ["DB_PATH"]
    # LOG_FILE = os.environ["LOG_FILE"]
    CONN_STRING = os.environ["DATABASE_URL"]
except Exception as e:
    print(f"Error getting variable from the environment: {e}.", file=sys.stderr)
    exit(1)

# Path to the transparent pixel
PIXEL_PATH = "pixel.png" 

# Create the FastAPI app instance
app = FastAPI()

@app.get("/view")
async def add_view_to_db(request: Request):
    """
    This endpoint logs the view and returns a 1x1 transparent pixel.
    """
    # 1. Get current time in UTC
    timestamp = datetime.now(timezone.utc).isoformat()

    # 2. Get request details (optional but great for analysis)
    user_agent = request.headers.get('user-agent')
    ip_address = request.client.host

    # 3. Save to the database
    try:
        with psycopg2.connect(CONN_STRING) as conn:
            print("Connection with database established.")

            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO page_views (timestamp, user_agent, ip_address) VALUES (?, ?, ?)",
                    (timestamp, user_agent, ip_address)
                )
                conn.commit()
                print("Successfully written to database.")

        # # Delete below
        # conn = sqlite3.connect(DB_PATH)
        # cursor = conn.cursor()
        # cursor.execute(
        #     "INSERT INTO page_views (timestamp, user_agent, ip_address) VALUES (?, ?, ?)",
        #     (timestamp, user_agent, ip_address)
        # )
        # conn.commit()
        # conn.close()
    except Exception as e:
        print(f"Error writing to database: {e}", file=sys.stderr)
        # with open(LOG_FILE, "a") as f:
        #     f.write(f"{timestamp},\"Error writing to database: {e}\"\n")

    # 4. Return the invisible pixel as a response
    # The media_type tells the browser it's a PNG image.
    return FileResponse(PIXEL_PATH, media_type="image/png")

# @app.get("/")
# def read_root():
#     """ A simple root endpoint to confirm the server is running. """
#     return {"message": "Hello! The view counting server is running."}

