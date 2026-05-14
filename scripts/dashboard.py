import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os

load_dotenv()

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────

st.set_page_config(
    page_title="Weather Pipeline Dashboard",
    page_icon="🌦️",
    layout="wide"
)

# ─────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────


# WITH this — hardcode localhost for the dashboard:
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="weather_pipeline",
        user="weather_user",
        password="weather_pass",
    )


@st.cache_data(ttl=300)  # refresh data every 5 minutes
def load_data():
    conn = get_connection()
    df = pd.read_sql(
        "SELECT * FROM weather_readings ORDER BY recorded_at DESC", conn)
    return df

# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────


df = load_data()

# Get the latest reading per city
latest = (
    df.sort_values("recorded_at")
      .groupby("city")
      .last()
      .reset_index()
)

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────

st.title("🌦️ Weather Pipeline Dashboard")
st.caption(
    "Live data · Auto-refreshes every 5 minutes · Built with Python, Airflow & PostgreSQL")
st.divider()

# ─────────────────────────────────────────
# TOP METRIC CARDS  (one per city)
# ─────────────────────────────────────────

st.subheader("Current conditions")
cols = st.columns(len(latest))

for col, (_, row) in zip(cols, latest.iterrows()):
    with col:
        st.metric(
            label=f"📍 {row['city']}, {row['country']}",
            value=f"{row['temp_c']}°C",
            delta=f"Feels {row['feels_like_c']}°C"
        )
        st.caption(f"💧 {row['humidity_pct']}%  💨 {row['wind_speed_ms']} m/s")
        st.caption(f"🌤 {row['weather_desc'].title()}")

st.divider()

# ─────────────────────────────────────────
# ROW 1:  Bar chart  +  Summary table
# ─────────────────────────────────────────

col1, col2 = st.columns([1.4, 1])

with col1:
    st.subheader("Temperature by city")
    fig_bar = px.bar(
        latest.sort_values("temp_c", ascending=False),
        x="city",
        y="temp_c",
        color="temp_c",
        color_continuous_scale="RdYlBu_r",
        labels={"temp_c": "Temp (°C)", "city": "City"},
        text="temp_c",
    )
    fig_bar.update_traces(texttemplate="%{text:.1f}°C", textposition="outside")
    fig_bar.update_layout(coloraxis_showscale=False, margin=dict(t=20))
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.subheader("City summary")
    summary = latest[[
        "city", "temp_c", "humidity_pct",
        "wind_speed_ms", "weather_desc"
    ]].rename(columns={
        "temp_c": "Temp °C",
        "humidity_pct": "Humidity %",
        "wind_speed_ms": "Wind m/s",
        "weather_desc": "Condition"
    })
    st.dataframe(summary, use_container_width=True, hide_index=True)

st.divider()

# ─────────────────────────────────────────
# ROW 2:  Line chart  (trend over time)
# ─────────────────────────────────────────

st.subheader("Temperature trend over time")

if len(df) > len(latest):
    fig_line = px.line(
        df.sort_values("recorded_at"),
        x="recorded_at",
        y="temp_c",
        color="city",
        labels={"temp_c": "Temp (°C)", "recorded_at": "Time", "city": "City"},
        markers=True,
    )
    fig_line.update_layout(margin=dict(t=20))
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("⏳ This chart fills up as Airflow runs more pipeline cycles. Check back in an hour!")

st.divider()

# ─────────────────────────────────────────
# ROW 3:  Humidity bar  +  Conditions pie
# ─────────────────────────────────────────

col3, col4 = st.columns(2)

with col3:
    st.subheader("Humidity by city")
    fig_hum = px.bar(
        latest.sort_values("humidity_pct", ascending=True),
        x="humidity_pct",
        y="city",
        orientation="h",
        color="humidity_pct",
        color_continuous_scale="Blues",
        labels={"humidity_pct": "Humidity (%)", "city": "City"},
    )
    fig_hum.update_layout(coloraxis_showscale=False, margin=dict(t=20))
    st.plotly_chart(fig_hum, use_container_width=True)

with col4:
    st.subheader("Weather conditions")
    conditions = df.groupby("weather_main").size().reset_index(name="count")
    fig_pie = px.pie(
        conditions,
        names="weather_main",
        values="count",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_pie.update_layout(margin=dict(t=20))
    st.plotly_chart(fig_pie, use_container_width=True)

# ─────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────

st.divider()
st.caption(
    f"Total readings in database: **{len(df)}**  |  Pipeline by Imasha  |  Data: OpenWeatherMap API")
