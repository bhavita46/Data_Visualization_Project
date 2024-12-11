# Ensuring `plotly, matplotlib and seaborn` are installed
import subprocess
import sys

# Function to install missing libraries (as it was noticed they required explicit installation)
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Installing required libraries
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

# Loading the filtered dataset for the map using caching
@st.cache_data
def load_map_data():
    map_data_path = "filtered_data_last_6_months_2024.csv"  
    return pd.read_csv(map_data_path)

# Loading the contextual data using caching
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

        # Using the correct datetime column: original_time_queued
        if "original_time_queued" in data.columns:
            data["datetime"] = pd.to_datetime(data["original_time_queued"], errors="coerce")
        else:
            st.error("No valid datetime column found in the dataset.")
            return pd.DataFrame()
        
        # Filtering for the last 6 months of 2024
        start_date = '2024-07-01'
        end_date = '2024-12-31'
        data = data[(data["datetime"] >= start_date) & (data["datetime"] <= end_date)]
        
        # Adding additional columns for analysis
        data["month"] = data["datetime"].dt.month
        data["year"] = data["datetime"].dt.year
        data["am_pm"] = data["datetime"].dt.hour.apply(lambda x: "AM" if x < 12 else "PM")
        return data
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()

# Visualizations
def plot_crime_count_by_precinct(data):
    st.subheader("Crime Count by Precinct")
    precinct_chart = px.bar(
        data.groupby("Precinct").size().reset_index(name="Crime Count"),
        x="Precinct",
        y="Crime Count",
        color="Precinct",
        title="Crime Count by Precinct",
        labels={"Precinct": "Police Precinct", "Crime Count": "Crime Count"},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    precinct_chart.update_layout(
        paper_bgcolor="black",
        plot_bgcolor="black",
        font_color="white",
        title_font_color="white",
    )
    st.plotly_chart(precinct_chart, use_container_width=True)

def plot_crime_categories_over_time(data):
    st.subheader("Crime Categories Over Time")
    time_series_chart = px.line(
        data.groupby(["Offense Start DateTime", "Crime Against Category"]).size().reset_index(name="Crime Count"),
        x="Offense Start DateTime",
        y="Crime Count",
        color="Crime Against Category",
        title="Crime Categories Over Time",
        labels={"Offense Start DateTime": "Date", "Crime Count": "Crime Count", "Crime Against Category": "Category"},
        line_shape="linear",
    )
    time_series_chart.update_layout(
        paper_bgcolor="black",
        plot_bgcolor="black",
        font_color="white",
        title_font_color="white",
    )
    st.plotly_chart(time_series_chart, use_container_width=True)

def plot_911_calls_by_month(data):
    st.subheader("911 Calls by Month (AM/PM)")
    month_grouped = data.groupby(["month", "am_pm"]).size().unstack(fill_value=0)
    month_grouped.index = month_grouped.index.map({7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'})  # Map month numbers to names
    fig, ax = plt.subplots(figsize=(10, 6))
    month_grouped.plot(kind="bar", stacked=True, color={"AM": "#4a90e2", "PM": "#e94e77"}, ax=ax)
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    ax.set_title("911 Calls by Month (AM/PM)", color="white", fontsize=16)
    ax.set_xlabel("Month", fontsize=14, color="white")
    ax.set_ylabel("Number of Calls", fontsize=14, color="white")
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    ax.legend(title="Time of Day", fontsize=12, title_fontsize=14, facecolor="black", edgecolor="white", labelcolor="white")
    st.pyplot(fig)


def plot_911_calls_by_month_line(data):
    st.subheader("911 Calls Per Month (July - December 2024)")
    month_grouped = data.groupby("month").size()
    month_grouped.index = month_grouped.index.map({7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'})  # Map month numbers to names
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(month_grouped.index, month_grouped.values, marker="o", linestyle="-", color="#e94e77", linewidth=2)
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    ax.set_title("911 Calls Per Month (July - December 2024)", color="white", fontsize=16)
    ax.set_xlabel("Month", fontsize=14, color="white")
    ax.set_ylabel("Number of Calls", fontsize=14, color="white")
    ax.grid(alpha=0.3, color="white")
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    st.pyplot(fig)

def plot_calls_by_priority_and_precinct(data):
    st.subheader("911 Calls by Precinct and Priority")
    priority_precinct_grouped = data.groupby(["precinct", "priority"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 6))
    priority_precinct_grouped.plot(kind="bar", stacked=True, colormap="viridis", ax=ax)
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    ax.set_title("911 Calls by Precinct and Priority", color="white", fontsize=16)
    ax.set_xlabel("Precinct", fontsize=14, color="white")
    ax.set_ylabel("Number of Calls", fontsize=14, color="white")
    ax.tick_params(axis="x", labelrotation=0, colors="white")
    ax.tick_params(axis="y", colors="white")
    legend = ax.legend(title="Priority", fontsize=12)
    legend.get_frame().set_facecolor("black")
    legend.get_frame().set_edgecolor("white")
    legend.set_title("Priority")
    legend.get_title().set_color("white")
    for text in legend.get_texts():
        text.set_color("white")
    st.pyplot(fig)

# Main Streamlit App
def main():
    # Loading data
    map_data = load_map_data()
    crime_data = fetch_crime_data(limit=50000)

    # Sidebar Filters
    st.sidebar.header("Filter Data")
    precinct_filter = st.sidebar.multiselect(
        "Select Precinct(s):",
        options=map_data["Precinct"].dropna().unique(),
        default=map_data["Precinct"].dropna().unique(),
    )
    category_filter = st.sidebar.multiselect(
        "Select Crime Category:",
        options=map_data["Crime Against Category"].dropna().unique(),
        default=map_data["Crime Against Category"].dropna().unique(),
    )

    # Apply Filters
    filtered_data = map_data[
        (map_data["Precinct"].isin(precinct_filter)) &
        (map_data["Crime Against Category"].isin(category_filter))
    ]

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
                data=filtered_data,
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

    # Crime Count by Precinct
    plot_crime_count_by_precinct(filtered_data)

    # Crime Categories Over Time
    plot_crime_categories_over_time(filtered_data)

    # Contextual Visualizations
    st.header("Contextual Visualizations of Seattle 911 Calls")

    if crime_data.empty:
        st.error("No data available.")
        return

    plot_911_calls_by_month(crime_data)
    plot_911_calls_by_month_line(crime_data)
    plot_calls_by_priority_and_precinct(crime_data)

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