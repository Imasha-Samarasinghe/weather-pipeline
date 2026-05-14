import os
import json
import logging
import pandas as pd
from datetime import datetime, timezone

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

RAW_DATA_DIR = "raw_data"
CLEAN_DATA_DIR = "clean_data"
LOG_DIR = "logs"

os.makedirs(CLEAN_DATA_DIR, exist_ok=True)

# ─────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"{LOG_DIR}/pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def unix_to_utc(unix_ts: int) -> str:
    """Convert a Unix timestamp integer to a readable UTC datetime string."""
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def parse_weather_record(data: dict) -> dict | None:
    """
    Extract and clean the fields we care about from one raw JSON dict.
    Returns a clean flat dictionary, or None if the data looks invalid.
    """
    try:
        record = {
            # Location
            "city":           data["name"],
            "country":        data["sys"]["country"],
            "latitude":       data["coord"]["lat"],
            "longitude":      data["coord"]["lon"],

            # Temperature
            "temp_c":         data["main"]["temp"],
            "feels_like_c":   data["main"]["feels_like"],
            "temp_min_c":     data["main"]["temp_min"],
            "temp_max_c":     data["main"]["temp_max"],

            # Atmosphere
            "humidity_pct":   data["main"]["humidity"],
            "pressure_hpa":   data["main"]["pressure"],
            # .get() = None if missing
            "visibility_m":   data.get("visibility"),

            # Wind
            "wind_speed_ms":  data["wind"]["speed"],
            "wind_gust_ms":   data["wind"].get("gust"),    # optional field

            # Conditions
            "weather_main":   data["weather"][0]["main"],
            "weather_desc":   data["weather"][0]["description"],
            "cloud_pct":      data["clouds"]["all"],

            # Rain (optional — only present when it's actually raining)
            "rain_1h_mm":     data.get("rain", {}).get("1h"),

            # Timestamps
            "recorded_at":    unix_to_utc(data["dt"]),
            "sunrise_utc":    unix_to_utc(data["sys"]["sunrise"]),
            "sunset_utc":     unix_to_utc(data["sys"]["sunset"]),

            # Track when OUR pipeline processed this record
            "processed_at":   datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        }
        return record

    except KeyError as e:
        logger.error(f"Missing expected field in JSON: {e}")
        return None


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def run_transform():
    logger.info("=" * 50)
    logger.info("Starting transform job")
    logger.info("=" * 50)

    json_files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith(".json")]

    if not json_files:
        logger.warning("No JSON files found in raw_data/. Run extract first.")
        return

    logger.info(f"Found {len(json_files)} raw JSON files to process")

    records = []

    for filename in json_files:
        filepath = os.path.join(RAW_DATA_DIR, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        record = parse_weather_record(raw_data)

        if record:
            records.append(record)
            logger.info(
                f"Parsed: {record['city']} | {record['temp_c']}°C | {record['weather_desc']}")
        else:
            logger.error(f"Skipped {filename} due to parse error")

    if not records:
        logger.warning("No valid records after transform. Nothing to save.")
        return

    # Convert list of dicts → pandas DataFrame
    df = pd.DataFrame(records)

    # Save as CSV with timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = os.path.join(
        CLEAN_DATA_DIR, f"weather_clean_{timestamp}.csv")
    df.to_csv(output_path, index=False)

    logger.info(f"Saved {len(df)} clean records to {output_path}")
    logger.info("Transform complete")

    # Print a preview in terminal so we can see the result
    print("\n--- CLEAN DATA PREVIEW ---")
    print(df[["city", "temp_c", "humidity_pct", "weather_desc",
          "recorded_at"]].to_string(index=False))
    print("--------------------------\n")


if __name__ == "__main__":
    run_transform()
