from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
import sys
import psycopg2
import httpx
from bs4 import BeautifulSoup
import json

load_dotenv()

# Get database connection string
try:
    CONN_STRING = os.environ["DATABASE_URL"]
except Exception as e:
    print(f"Error getting variable from the environment: {e}.", file=sys.stderr)
    exit(1)

# Path to the transparent pixel
PIXEL_PATH = "pixel.png" 

# The alt text of the counter image. This is how we'll find it on GitHub profile HTML.
IMAGE_ALT_TEXT = "Page views counter"

# How long to cache the camo URL before re-fetching it
CACHE_DURATION = timedelta(hours=24)

# In-Memory cache for GitHub camo URL
# This avoids scraping GitHub on every single request.
camo_url_cache = {
    "url": None,
    "timestamp": None # Type datetime, not str
}

# Persistent file cache
CACHE_DIR = os.getenv("CACHE_DIR")
CACHE_FILE_NAME = "camo_url_cache.json"

# Create the FastAPI app instance
app = FastAPI()

def read_cache_from_file() -> dict | None:
    """Reads the cache data from the JSON file."""
    if not CACHE_DIR:
        print("Cannot read from cache file. CACHE_DIR is not set in the environment.")
        return None

    cache_file_path = os.path.join(CACHE_DIR, CACHE_FILE_NAME)

    if not os.path.exists(cache_file_path):
        print("Cache file does not exist.")
        return None
    
    try:
        with open(cache_file_path, "r") as f:
            cache_data = json.load(f)
            # Basic validation
            if "url" in cache_data and "timestamp" in cache_data:
                camo_url_cache["timestamp"] = datetime.fromisoformat(cache_data["timestamp"])
                camo_url_cache["url"] = cache_data["url"]
                return cache_data
            else:
                print("Cache file is malformed.", file=sys.stderr)
                return None
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading or parsing cache file: {e}", file=sys.stderr)
        return None

def write_cache_to_file(url: str):
    """(Atomically) writes the new cache data to the JSON file."""

    camo_url_cache["url"] = url
    camo_url_cache["timestamp"] = datetime.now(timezone.utc)

    cache_to_write = {
        "url": camo_url_cache.get("url"),
        "timestamp": camo_url_cache.get("timestamp").isoformat() # Use ISO format for JSON
    }

    if not CACHE_DIR:
        print("Cannot write to cache file. CACHE_DIR is not set in the environment.")
        return

    cache_file_path = os.path.join(CACHE_DIR, CACHE_FILE_NAME)
    
    # # Atomic write: write to a temp file then rename
    # temp_file_path = cache_file_path + ".tmp"
    try:
        with open(cache_file_path, "w") as f:
            json.dump(cache_to_write, f)
        # os.rename(temp_file_path, cache_file_path)
        print(f"Successfully wrote new cache to {cache_file_path}")
    except Exception as e:
        print(f"Error writing to cache file: {e}", file=sys.stderr)

async def get_camo_url_from_github() -> str | None:
    """
    Scrapes the GitHub profile page to find the current camo URL for the view counter image.
    """
    github_profile_url = os.getenv("GITHUB_PROFILE_URL")
    if not github_profile_url:
        print("GITHUB_PROFILE_URL not found in the environment. Attempting to get last known GITHUB_CAMO_URL")
        return os.getenv("GITHUB_CAMO_URL")

    print(f"Attempting to fetch new camo URL from {github_profile_url}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(github_profile_url, follow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            # Find the <img> tag with the specific alt text
            img_tag = soup.find("img", alt=IMAGE_ALT_TEXT)

            if img_tag and img_tag.get("src"):
                camo_url = img_tag["src"]
                print(f"Successfully found camo URL: {camo_url}")
                # Update the cache
                write_cache_to_file(camo_url)
                return camo_url
            else:
                print(f"Could not find an <img> tag with alt='{IMAGE_ALT_TEXT}'", file=sys.stderr)
                return None
    except Exception as e:
        print(f"Error fetching or parsing GitHub profile: {e}", file=sys.stderr)
        return None

async def get_cached_camo_url():
    """
    Returns the cached camo URL. If the cache is empty or stale, it triggers a refresh.
    """
    read_cache_from_file() # sets the global camo_url_cache

    now = datetime.now(timezone.utc)
    cached_time = camo_url_cache["timestamp"]

    if not camo_url_cache.get("url") or not cached_time or (now - cached_time > CACHE_DURATION):
        print("Cache is stale or empty. Refreshing camo URL.")
        return await get_camo_url_from_github()
    
    print("Returning camo URL from cache.")
    return camo_url_cache["url"]

async def purge_github_cache():
    """
    Gets the camo URL (from cache or by fetching) and sends a PURGE request.
    This runs in the background.
    """
    camo_url = await get_cached_camo_url()
    if not camo_url:
        print("No camo URL available. Skipping cache purge.", file=sys.stderr)
        return
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"Attempting to purge cache for: {camo_url}")
            response = await client.request("PURGE", camo_url)
            response.raise_for_status()
            print(f"Successfully purged cache. Status: {response.status_code}")

    except httpx.HTTPStatusError as e:
        print(f"Error purging GitHub cache: Status {e.response.status_code} for URL {e.request.url}", file=sys.stderr)
    except Exception as e:
        print(f"Error purging GitHub cache: {e}", file=sys.stderr)

@app.get("/view")
async def add_view_to_db(request: Request, background_tasks: BackgroundTasks):
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
                    "INSERT INTO page_views (timestamp, user_agent, ip_address) VALUES (%s, %s, %s)",
                    (timestamp, user_agent, ip_address)
                )
                conn.commit()
                print("Successfully written to database.")

    except Exception as e:
        print(f"Error writing to database: {e}", file=sys.stderr)

    # 4. Add a background task to purge GitHub image cache *after* returning the image below
    background_tasks.add_task(purge_github_cache);

    # 5. Return the invisible pixel as a response
    # The media_type tells the browser it's a PNG image.
    return FileResponse(PIXEL_PATH, media_type="image/png")

# @app.get("/")
# def read_root():
#     """ A simple root endpoint to confirm the server is running. """
#     return {"message": "Hello! The view counting server is running."}

# Add a root endpoint for basic health checks
@app.get("/")
def read_root():
    return {"status": "ok"}
