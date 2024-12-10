import streamlit as st
import pandas as pd
import pydeck as pdk

# Title for the app
st.title("Seattle Crime Map (July - December 2024)")
st.write("Visualization by Vikramjeet Singh Kundu")

# Load the filtered dataset using the updated caching function
@st.cache_data
def load_data():
    data_path = "filtered_last_6_months_2024.csv"  # Ensure this file is in the same directory
    data = pd.read_csv(data_path)
    return data

data = load_data()

# Map visualization
st.subheader("Interactive Crime Location Map")
st.write("This map shows the reported crimes in Seattle for the last six months of 2024. Hover over a point to view the type of crime.")

# Define Pydeck map configuration with focus on Seattle and top-down view
seattle_lat, seattle_lon = 47.608013, -122.335167  # Coordinates for Seattle
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
        latitude=seattle_lat,
        longitude=seattle_lon,
        zoom=12,  # Adjusted zoom level for better focus on Seattle
        pitch=0,  # Top-down view
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=data,
            get_position='[Longitude, Latitude]',
            get_color='[200, 30, 0, 160]',
            get_radius=50,
            pickable=True,  # Enables interactivity on hover
        ),
        pdk.Layer(
            "TextLayer",
            data=data,
            get_position='[Longitude, Latitude]',
            get_text='"Offense"',  # Display the type of offense
            get_size=12,
            get_color='[0, 0, 0, 255]',
            get_alignment_baseline="'bottom'",
        ),
    ],
    tooltip={
        "html": "<b>Crime Type:</b> {Offense}<br><b>Location:</b> {100 Block Address}",
        "style": {"color": "white"}
    },
))