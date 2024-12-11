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
    map_data_path = "filtered_data_last_6_months_2024.csv" 
    return pd.read_csv(map_data_path)

# Load contextual data using caching
@st.cache_data
def load_contextual_data():
    context_data_path = 'SPD_Crime_Data__2008-Present_20241122 (1).csv' 
    data = pd.read_csv(context_data_path)
    data['Offense Start DateTime'] = pd.to_datetime(data['Offense Start DateTime'], errors='coerce')
    data['Year'] = data['Offense Start DateTime'].dt.year
    data = data.dropna(subset=['Year'])
    data['Year'] = data['Year'].astype(int)
    data = data[data['Year'] > 2020]
    data.rename(columns={'Latitude': 'latitude', 'Longitude': 'longitude'}, inplace=True)
    return data

map_data = load_map_data()
context_data = load_contextual_data()

# Map visualization
st.header("Interactive Crime Location Map")
st.write("Hover over a point to view the details of the reported crimes.")
seattle_lat, seattle_lon = 47.608013, -122.335167  # Coordinates for Seattle
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
        latitude=seattle_lat,
        longitude=seattle_lon,
        zoom=12,
        pitch=0,  # Top-down view
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=map_data,
            get_position='[Longitude, Latitude]',
            get_color='[200, 30, 0, 160]',
            get_radius=50,
            pickable=True,  # Enables interactivity on hover
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

# Contextual visualizations
st.header("Contextual Visualizations")
st.sidebar.header("Filter Data")
selected_year = st.sidebar.multiselect(
    "Select Year(s):",
    options=context_data['Year'].unique().tolist(),
    default=context_data['Year'].unique().tolist()
)
selected_precinct = st.sidebar.multiselect(
    "Select Precinct(s):",
    options=context_data['Precinct'].dropna().unique(),
    default=context_data['Precinct'].dropna().unique()
)
selected_category = st.sidebar.multiselect(
    "Select Crime Category:",
    options=context_data['Crime Against Category'].dropna().unique(),
    default=context_data['Crime Against Category'].dropna().unique()
)

# Filter contextual data
context_data_filtered = context_data[
    (context_data['Year'].isin(selected_year)) &
    (context_data['Precinct'].isin(selected_precinct)) &
    (context_data['Crime Against Category'].isin(selected_category))
]

# Crime Count by Precinct
st.subheader("Crime Count by Precinct")
precinct_chart = px.bar(
    context_data_filtered.groupby('Precinct').size().reset_index(name='Count'),
    x='Precinct',
    y='Count',
    title="Crime Count by Precinct",
    labels={'Count': 'Crime Count', 'Precinct': 'Police Precinct'},
    color='Precinct'
)
st.plotly_chart(precinct_chart, use_container_width=True)

# Crime Categories Over Time
st.subheader("Crime Categories Over Time")
time_series_chart = px.line(
    context_data_filtered.groupby(['Year', 'Crime Against Category']).size().reset_index(name='Count'),
    x='Year',
    y='Count',
    color='Crime Against Category',
    title="Crime Categories Over Time",
    labels={'Year': 'Year', 'Count': 'Crime Count', 'Crime Against Category': 'Category'},
    line_shape="linear"
)
time_series_chart.update_layout(xaxis=dict(type='category'))  # Force categorical x-axis
st.plotly_chart(time_series_chart, use_container_width=True)

st.write("""
This visualization provides an interactive exploration of crime trends in Seattle, segmented by precinct and crime category. 
The bar chart highlights the distribution of crime counts across precincts, while the line chart shows trends in crime categories over time. 
""")