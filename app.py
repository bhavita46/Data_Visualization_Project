
import streamlit as st
import pandas as pd
import pydeck as pdk

# Title for the app
st.title("Seattle Crime Map (July - December 2024)")
st.write("Visualization by Vikramjeet Singh Kundu")

# Load the filtered dataset
@st.cache
def load_data():
    data_path = "filtered_data_last_6_months_2024.csv"  
    data = pd.read_csv(data_path)
    return data

data = load_data()

# Map visualization
st.subheader("Interactive Crime Location Map")
st.write("This map shows the reported crimes in Seattle for the last six months of 2024.")

# Define Pydeck map configuration
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
        latitude=data['Latitude'].mean(),
        longitude=data['Longitude'].mean(),
        zoom=11,
        pitch=50,
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=data,
            get_position='[Longitude, Latitude]',
            get_color='[200, 30, 0, 160]',
            get_radius=50,
        ),
    ],
))
