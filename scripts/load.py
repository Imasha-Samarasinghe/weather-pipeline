import os
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from datetime import datetime

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST"),
    "port":     os.getenv("DB_PORT"),
    "dbname":   os.getenv("DB_NAME"),
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

CLEAN_DATA_DIR = "clean_data"
LOG_DIR        = "logs"

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
# DATABASE FUNCTIONS
# ─────────────────────────────────────────

def get_connection():
    """Create and return a database connection."""
    conn = psycopg2.connect(**DB_CONFIG)
    logger.info("Connected to PostgreSQL")
    return conn


def create_table(conn):
    """
    Create the weather_readings table if it doesn't already exist.
    Running this every time is safe — CREATE TABLE IF NOT EXISTS won't
    overwrite existing data.
    """
    sql = """
    CREATE TABLE IF NOT EXISTS weather_readings (
        id              SERIAL PRIMARY KEY,
        city            VARCHAR(100)   NOT NULL,
        country         VARCHAR(10),
        latitude        NUMERIC(9, 4),
        longitude       NUMERIC(9, 4),
        temp_c          NUMERIC(6, 2),
        feels_like_c    NUMERIC(6, 2),
        temp_min_c      NUMERIC(6, 2),
        temp_max_c      NUMERIC(6, 2),
        humidity_pct    INTEGER,
        pressure_hpa    INTEGER,
        visibility_m    INTEGER,
        wind_speed_ms   NUMERIC(6, 2),
        wind_gust_ms    NUMERIC(6, 2),
        weather_main    VARCHAR(50),
        weather_desc    VARCHAR(100),
        cloud_pct       INTEGER,
        rain_1h_mm      NUMERIC(6, 2),
        recorded_at     TIMESTAMP,
        sunrise_utc     TIMESTAMP,
        sunset_utc      TIMESTAMP,
        processed_at    TIMESTAMP
    );
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        conn.commit()
    logger.info("Table 'weather_readings' ready")


def insert_records(conn, df: pd.DataFrame):
    """
    Insert all rows from the DataFrame into weather_readings.
    Uses execute_values for efficient bulk insert.
    """
    # Replace pandas NaN with None (which becomes NULL in PostgreSQL)
    df = df.where(pd.notnull(df), None)

    columns = [
        "city", "country", "latitude", "longitude",
        "temp_c", "feels_like_c", "temp_min_c", "temp_max_c",
        "humidity_pct", "pressure_hpa", "visibility_m",
        "wind_speed_ms", "wind_gust_ms",
        "weather_main", "weather_desc", "cloud_pct", "rain_1h_mm",
        "recorded_at", "sunrise_utc", "sunset_utc", "processed_at"
    ]

    # Convert DataFrame rows to list of tuples
    values = [tuple(row[col] for col in columns) for _, row in df.iterrows()]

    sql = f"""
        INSERT INTO weather_readings ({', '.join(columns)})
        VALUES %s
    """

    with conn.cursor() as cur:
        execute_values(cur, sql, values)
        conn.commit()

    logger.info(f"Inserted {len(values)} rows into weather_readings")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def run_load():
    logger.info("=" * 50)
    logger.info("Starting load job")
    logger.info("=" * 50)

    # Find the most recent clean CSV
    csv_files = sorted([
        f for f in os.listdir(CLEAN_DATA_DIR) if f.endswith(".csv")
    ])

    if not csv_files:
        logger.warning("No CSV files found in clean_data/. Run transform first.")
        return

    latest_csv = os.path.join(CLEAN_DATA_DIR, csv_files[-1])
    logger.info(f"Loading file: {latest_csv}")

    df = pd.read_csv(latest_csv)
    logger.info(f"Read {len(df)} rows from CSV")

    conn = get_connection()

    try:
        create_table(conn)
        insert_records(conn, df)
        logger.info("Load job complete")

    except Exception as e:
        logger.error(f"Load failed: {e}")
        conn.rollback()

    finally:
        conn.close()
        logger.info("Database connection closed")


if __name__ == "__main__":
    run_load()