# Ensuring `plotly, matplotlib and seaborn` are installed
import subprocess
import sys

# Function to install missing libraries
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required libraries
try:
    import plotly.express as px
except ImportError:
    install("plotly")

try:
    import matplotlib.pyplot as plt
except ImportError:
    install("matplotlib")

try:
    import seaborn as sns
except ImportError:
    install("seaborn")

import streamlit as st
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
import plotly.express as px
import requests
import seaborn as sns

# Title for the app
st.title("Seattle Crime Data Visualization")
st.write("Visualization by Bhavita Vijay Bhoir, Rekha Kandukuri, Shefali Saxena, and Vikramjeet Singh Kundu")

# Load the filtered dataset for the map using caching
@st.cache_data
def load_map_data():
    map_data_path = "filtered_data_last_6_months_2024.csv"  # Ensure this file is in the same directory
    return pd.read_csv(map_data_path)

# Load contextual data using caching
@st.cache_data
def fetch_crime_data(limit=50000):
    API_URL = "https://data.seattle.gov/resource/33kz-ixgy.json"
    params = {
        "$limit": limit,
        "$where": "blurred_longitude != '-1' AND blurred_latitude != '-1'",
    }
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        data = pd.DataFrame(response.json())
        data["datetime"] = pd.to_datetime(data["event_clearance_date"], errors="coerce")
        data["month"] = data["datetime"].dt.month
        data["year"] = data["datetime"].dt.year
        data["am_pm"] = data["datetime"].dt.hour.apply(lambda x: "AM" if x < 12 else "PM")
        return data
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()

# Visualizations
def plot_911_calls_by_month(data):
    st.subheader("911 Calls by Month (AM/PM)")
    month_grouped = data.groupby(["month", "am_pm"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 6))
    month_grouped.plot(kind="bar", stacked=True, ax=ax)
    ax.set_title("911 Calls by Month (AM/PM)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of Calls")
    st.pyplot(fig)

def plot_911_calls_by_year(data):
    st.subheader("911 Calls by Year")
    year_grouped = data.groupby("year").size()
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(year_grouped.index, year_grouped.values, marker="o", linestyle="-")
    ax.set_title("911 Calls by Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Calls")
    st.pyplot(fig)

def plot_calls_by_priority_and_precinct(data):
    st.subheader("911 Calls by Precinct and Priority")
    priority_precinct_grouped = data.groupby(["precinct", "priority"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 6))
    priority_precinct_grouped.plot(kind="bar", stacked=True, ax=ax)
    ax.set_title("911 Calls by Precinct and Priority")
    ax.set_xlabel("Precinct")
    ax.set_ylabel("Number of Calls")
    st.pyplot(fig)

# Main Streamlit App
def main():
    # Load data
    map_data = load_map_data()
    crime_data = fetch_crime_data(limit=50000)

    # Map Visualization
    st.header("Interactive Crime Location Map")
    st.write("This map shows reported crimes in Seattle for the last six months of 2024.")
    seattle_lat, seattle_lon = 47.608013, -122.335167  # Coordinates for Seattle
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=seattle_lat,
            longitude=seattle_lon,
            zoom=12,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=map_data,
                get_position='[Longitude, Latitude]',
                get_color='[200, 30, 0, 160]',
                get_radius=50,
                pickable=True,
            ),
        ],
        tooltip={
            "html": """
            <b>Crime Type:</b> {Offense}<br>
            <b>Location:</b> {100 Block Address}<br>
            <b>Date:</b> {Offense Start DateTime}
            """,
            "style": {"color": "white"}
        },
    ))

    # Contextual Visualizations
    st.header("Contextual Visualizations of Seattle 911 Calls")

    if crime_data.empty:
        st.error("No data available.")
        return

    plot_911_calls_by_month(crime_data)
    st.write("""This stacked bar chart divides emergency calls into morning (AM) and evening (PM) categories for each month of the year.""")

    plot_911_calls_by_year(crime_data)
    st.write("""The line chart illustrates annual variations in emergency call volumes.""")

    plot_calls_by_priority_and_precinct(crime_data)
    st.write("""This stacked bar chart highlights the distribution of calls by precinct and their assigned priority levels.""")

    # Data Citations
    st.subheader("**Data Sources**")
    st.write("**1. Primary Dataset:**")
    st.write("Dataset: [Seattle Crime Data](https://data.seattle.gov/Public-Safety/SPD-Crime-Data-2008-Present/tazs-3rd5/about_data)")
    st.write("License: Public Domain")
    st.write("**2. Contextual Dataset:**")
    st.write("Dataset: [Seattle Calls Data](https://data.seattle.gov/Public-Safety/Call-Data/33kz-ixgy/data)")
    st.write("License: Public Domain")

if __name__ == "__main__":
    main()