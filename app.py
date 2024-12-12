# Ensuring plotly, matplotlib and seaborn are installed
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

# Updated precinct mapping
precinct_mapping = {
    "E": "East",
    "N": "North",
    "S": "South",
    "SW": "Southwest",
    "W": "West",
    "UNKNOWN": "Unknown"
}

# Set minimal style and keep dark background
sns.set(style="white")
plt.rcParams["figure.facecolor"] = "black"
plt.rcParams["axes.facecolor"] = "black"

def get_contrasting_colors(n, palette="viridis"):
    max_base = max(8, n * 2)
    colors_full = sns.color_palette(palette, n_colors=max_base)
    if n == 1:
        return [colors_full[len(colors_full)//2]]
    else:
        indices = [round(i*(len(colors_full)-1)/(n-1)) for i in range(n)]
        return [colors_full[i] for i in indices]

@st.cache_data
def load_map_data():
    map_data_path = "filtered_data_last_6_months_2024.csv"  
    data = pd.read_csv(map_data_path)
    if "Precinct" in data.columns:
        data["Precinct"] = data["Precinct"].replace(precinct_mapping)
    return data

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

        if "original_time_queued" in data.columns:
            data["datetime"] = pd.to_datetime(data["original_time_queued"], errors="coerce")
        else:
            st.error("No valid datetime column found in the dataset.")
            return pd.DataFrame()
        
        start_date = '2024-07-01'
        end_date = '2024-12-31'
        data = data[(data["datetime"] >= start_date) & (data["datetime"] <= end_date)]
        
        data["month"] = data["datetime"].dt.month
        data["year"] = data["datetime"].dt.year
        data["am_pm"] = data["datetime"].dt.hour.apply(lambda x: "AM" if x < 12 else "PM")

        if "precinct" in data.columns:
            data["precinct"] = data["precinct"].replace(precinct_mapping)

        return data
    else:
        st.error(f"Failed to fetch data: {response.status_code}")
        return pd.DataFrame()

def plot_crime_count_by_precinct(data):
    precinct_grouped = data.groupby("Precinct").size().reset_index(name="Crime Count")
    precincts = precinct_grouped["Precinct"].unique()
    precinct_colors = get_contrasting_colors(len(precincts), palette="viridis")
    precinct_plotly_colors = [
        f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})" for (r, g, b) in precinct_colors
    ]

    precinct_chart = px.bar(
        precinct_grouped,
        x="Precinct",
        y="Crime Count",
        color="Precinct",
        title="Crime Count by Precinct",
        labels={"Precinct": "Police Precinct", "Crime Count": "Crime Count"},
        color_discrete_sequence=precinct_plotly_colors,
    )
    precinct_chart.update_layout(
        paper_bgcolor="black",
        plot_bgcolor="black",
        font_color="white",
        title_font_color="white",
        legend_title="Precinct",
        xaxis=dict(showline=False, showgrid=False, zeroline=False),
        yaxis=dict(showline=False, showgrid=False, zeroline=False),
    )
    st.plotly_chart(precinct_chart, use_container_width=True)

def plot_911_calls_by_month(data):
    month_grouped = data.groupby(["month", "am_pm"]).size().unstack(fill_value=0)
    month_grouped.index = month_grouped.index.map({7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'})  

    large_palette = sns.color_palette("viridis", n_colors=10)
    am_color = large_palette[0]     
    pm_color = large_palette[-1]    

    fig, ax = plt.subplots(figsize=(10, 6))
    month_grouped.plot(
        kind="bar",
        stacked=True,
        color=[am_color, pm_color],
        ax=ax
    )
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    ax.set_title("911 Calls by Month (AM/PM)", color="white", fontsize=16)
    ax.set_xlabel("Month", fontsize=14, color="white")
    ax.set_ylabel("Number of Calls", fontsize=14, color="white")
    ax.tick_params(axis="x", colors="white", rotation=0)
    ax.tick_params(axis="y", colors="white")

    sns.despine(fig=fig, ax=ax, top=True, right=True, left=False, bottom=False)
    ax.grid(False)

    legend = ax.legend(title="Time of Day", fontsize=12, title_fontsize=14)
    legend.get_frame().set_facecolor("black")
    legend.get_frame().set_edgecolor("black")
    for text in legend.get_texts():
        text.set_color("white")
    legend.get_title().set_color("white")

    st.pyplot(fig)

def plot_calls_by_priority_and_precinct(data):
    if "precinct" in data.columns and "priority" in data.columns:
        priority_precinct_grouped = data.groupby(["precinct", "priority"]).size().unstack(fill_value=0)
        
        num_priorities = len(priority_precinct_grouped.columns)
        colors = get_contrasting_colors(num_priorities, palette="viridis")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        priority_precinct_grouped.plot(
            kind="bar", 
            stacked=True, 
            color=colors,
            ax=ax
        )
        fig.patch.set_facecolor("black")
        ax.set_facecolor("black")
        ax.set_title("911 Calls by Precinct and Priority", color="white", fontsize=16)
        ax.set_xlabel("Precinct", fontsize=14, color="white")
        ax.set_ylabel("Number of Calls", fontsize=14, color="white")
        ax.tick_params(axis="x", labelrotation=0, colors="white")
        ax.tick_params(axis="y", colors="white")

        sns.despine(fig=fig, ax=ax, top=True, right=True, left=False, bottom=False)
        ax.grid(False)

        legend = ax.legend(title="Priority", fontsize=12, loc='center left', bbox_to_anchor=(1, 0.5))
        legend.get_frame().set_facecolor("black")
        legend.get_frame().set_edgecolor("black")
        legend.set_title("Priority")
        legend.get_title().set_color("white")
        for text in legend.get_texts():
            text.set_color("white")

        st.pyplot(fig)
    else:
        st.write("Priority or precinct data not available.")

def main():
    map_data = load_map_data()
    crime_data = fetch_crime_data(limit=50000)

    st.title("seattle crim data visualization")
    st.write("*By Bhavita Vijay Bhoir, Rekha Kandukuri, Shefali Saxena, and Vikramjeet Singh Kundu*")

    st.markdown("""**Introduction**  
Seattle’s diverse neighborhoods exhibit a range of public safety conditions, influenced by factors such as population density, commercial activity, and local infrastructure. Analyzing crime data in a way that is accessible, clear, and meaningful can inform policy decisions, resource allocation, and community engagement strategies. In an effort to render complex data more understandable, we present a series of visualizations that transform raw crime and emergency call data into a suite of interactive, interpretable tools for both stakeholders and the general public.

The materials presented here integrate spatial, temporal, and categorical dimensions of crime and emergency responses, facilitating a more comprehensive understanding of Seattle’s public safety landscape. By examining these visual representations, readers can better appreciate patterns of criminal activity, distributions of reported incidents, and the dynamics of 911 call priorities. This holistic approach aims to support dialogue and decision-making grounded in empirical evidence.
""")

    # Sidebar Filters
    st.sidebar.header("Filter Data")
    precinct_options = map_data["Precinct"].dropna().unique()
    precinct_filter = st.sidebar.multiselect(
        "Select Precinct(s):",
        options=precinct_options,
        default=precinct_options,
    )

    filtered_data = map_data[map_data["Precinct"].isin(precinct_filter)]

    # More blue-ish tone from viridis:
    viridis_point_color = [39, 127, 142, 160]

    st.markdown("""**Interative crime location map**  
The central element of this presentation is an interactive map depicting reported crime incidents in Seattle during the final six months of 2024. Each point on the map corresponds to a reported crime, enriched with details regarding the nature of the offense, its approximate location, and the associated date. Users can filter these data points by precinct, thereby enabling focused exploration of specific localities.

This cartographic representation allows viewers to discern spatial patterns that might otherwise remain opaque. The map’s dark background and carefully selected bluish hue for the markers create a high-contrast visual environment, ensuring legibility and drawing the eye to areas of concentrated activity. Such geographic context is critical: the distribution of criminal incidents often correlates with neighborhood characteristics, transportation hubs, or economic centers.
""")

    st.write("This map shows reported crimes in Seattle for the last six months of 2024.")
    seattle_lat, seattle_lon = 47.608013, -122.335167
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v9',
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
                get_color=viridis_point_color,
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

    st.markdown("""**Crime Count by Precinct**  
Complementing the map, a bar chart visualizing the total crime count by precinct provides a categorical summary of incident frequency. Each bar corresponds to a particular precinct, enabling users to compare relative crime levels across different segments of the city.

This representation offers a stable reference point. While the map conveys geographic nuance, the bar chart isolates and highlights the scale of reported crimes in each jurisdiction. In doing so, it fosters a straightforward understanding of where incident volume may be highest, prompting questions about underlying factors influencing these differences.
""")

    plot_crime_count_by_precinct(filtered_data)

    st.markdown("""**911 Calls by Month (AM/PM)**  
Temporal patterns are equally critical to a thorough interpretation of public safety data. The stacked bar chart of 911 calls by month, separated into AM and PM intervals, illustrates how call volumes fluctuate over time. By examining differences in morning versus evening call counts, one may identify seasonal trends or time-of-day patterns that influence public safety demands.

This temporal dimension enhances the context provided by the map and the precinct-based counts, suggesting when emergency resources may be most strained. Seasonal peaks or consistent nocturnal increases in call volume can inform resource scheduling and preventive measures.
""")

    

    if crime_data.empty:
        st.error("No data available.")
        return

    plot_911_calls_by_month(crime_data)

    st.markdown("""**911 Calls by Precinct and Priority**  
To further deepen our understanding of the data, we present a stacked bar chart detailing 911 calls by precinct, differentiated by priority level. This visual delineates not only how many calls a given precinct receives, but also the nature of those calls in terms of urgency.

By viewing priority levels alongside geographic segments, one can ascertain whether certain precincts routinely handle more high-priority, time-sensitive incidents. This insight adds explanatory power to the raw crime counts: understanding that some areas manage a higher proportion of critical calls may indicate differing types of challenges and may justify a reevaluation of resource distribution strategies.
""")

    plot_calls_by_priority_and_precinct(crime_data)

    st.markdown("""**Inspiration and Additional Context**  
In designing these contextual visualizations, we drew inspiration from approaches employed elsewhere, including the strategies showcased at [this reference link](https://rpubs.com/swalsh114/1006412). Observing the effective use of color, composition, and data structuring in external examples informed our design decisions, ensuring that our representations are both rigorous and accessible.

The integration of multiple data dimensions—spatial, temporal, and categorical—enables a more nuanced reading of Seattle’s crime and emergency call landscape. For instance, while the “Crime Count by Precinct” chart identifies areas with higher incident frequencies, the priority-level breakdown and monthly call distributions contextualize these figures. Together, these visuals present a multidimensional narrative that moves beyond static counts, supporting informed debate, policy formulation, and resource prioritization.
""")

    # Data Citations
    st.subheader("**Data Sources and References**")
    st.write("**Primary Dataset (Crime Data):** [Seattle Crime Data (Public Domain)](https://data.seattle.gov/Public-Safety/SPD-Crime-Data-2008-Present/tazs-3rd5/about_data)")
    st.write("**Contextual Dataset (911 Calls):** [Seattle Calls Data (Public Domain)](https://data.seattle.gov/Public-Safety/Call-Data/33kz-ixgy/data)")
    st.write("**Visualization Inspiration:** [https://rpubs.com/swalsh114/1006412](https://rpubs.com/swalsh114/1006412)")

if __name__ == "__main__":
    main()
