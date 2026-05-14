import requests
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Cities we want to track - you can add or change these
CITIES = [
    "London",
    "Colombo",
    "New York",
    "Tokyo",
    "Sydney",
    "Seoul"
]

# Folders
RAW_DATA_DIR = "raw_data"
LOG_DIR = "logs"

# ─────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"{LOG_DIR}/pipeline.log",
                            encoding="utf-8"),  # writes to file
        logging.StreamHandler()                           # also prints to terminal
    ]
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# FUNCTIONS
# ─────────────────────────────────────────

def fetch_weather(city: str) -> dict | None:
    """
    Fetch current weather for a single city.
    Returns the JSON data as a dict, or None if the call failed.
    """
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"   # gives us Celsius
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()  # raises an error for 4xx/5xx responses
        logger.info(f"✅ Successfully fetched weather for {city}")
        return response.json()

    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ HTTP error for {city}: {e}")
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Connection error for {city} — check your internet")
    except requests.exceptions.Timeout:
        logger.error(f"❌ Request timed out for {city}")

    return None  # return None if anything went wrong


def save_raw_json(city: str, data: dict) -> str:
    """
    Save raw API response to a JSON file.
    Filename includes city and timestamp so nothing gets overwritten.
    Returns the file path.
    """
    # Create a timestamp string like: 2024-05-14_13-45-00
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")

    # Clean city name for filename (e.g. "New York" → "new_york")
    city_slug = city.lower().replace(" ", "_")

    filename = f"{city_slug}_{timestamp}.json"
    filepath = os.path.join(RAW_DATA_DIR, filename)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"💾 Saved raw data to {filepath}")
    return filepath


def run_extract():
    """
    Main extract function — loops through all cities,
    fetches data, and saves raw JSON files.
    """
    logger.info("=" * 50)
    logger.info("Starting extract job")
    logger.info(f"Cities: {CITIES}")
    logger.info("=" * 50)

    success_count = 0
    fail_count = 0

    for city in CITIES:
        data = fetch_weather(city)

        if data:
            save_raw_json(city, data)
            success_count += 1
        else:
            fail_count += 1

    logger.info(
        f"Extract complete — {success_count} succeeded, {fail_count} failed")


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────

if __name__ == "__main__":
    run_extract()
