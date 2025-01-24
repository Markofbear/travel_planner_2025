import os
from datetime import datetime

import folium
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from plot_maps import TripMap
from streamlit_folium import st_folium

from backend.connect_to_api import ResRobot, get_weather
from backend.trips import TripPlanner

# Default coordinates and city for the map
DEFAULT_COORDS = {
    "lat": 57.7089,
    "lon": 11.9746,
}  # Latitude and Longitude for Gothenburg
DEFAULT_CITY = "Göteborg"

# Load environment variables from .env file
load_dotenv()

# Fetch the OpenWeather API key from the .env file
OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")


def display_default_map():
    """
    Display a default map centered on Gothenburg with no trip markers.
    """
    folium_map = folium.Map(
        location=[DEFAULT_COORDS["lat"], DEFAULT_COORDS["lon"]], zoom_start=12
    )

    folium.Marker(
        location=[DEFAULT_COORDS["lat"], DEFAULT_COORDS["lon"]],
        popup="Gothenburg (Göteborg)",
    ).add_to(folium_map)

    st_folium(folium_map, width=700, height=500)


def weather_section(city_name):
    """
    Display the weather for a given city.
    If no city is provided, default to Gothenburg.
    """
    if not OPEN_WEATHER_API_KEY:
        st.error("Ingen API-nyckel hittades för OpenWeather. Kontrollera din .env-fil.")
        return

    # Fetch weather data
    weather_data = get_weather(city_name, OPEN_WEATHER_API_KEY)

    if weather_data:
        st.subheader(
            f"Vädret i {weather_data['name']}, {weather_data['sys']['country']}"
        )
        st.write(f"**Temperatur**: {weather_data['main']['temp']}°C")
        st.write(f"**Känns som**: {weather_data['main']['feels_like']}°C")
        st.write(f"**Väder**: {weather_data['weather'][0]['description'].capitalize()}")
        st.write(f"**Luftfuktighet**: {weather_data['main']['humidity']}%")
        st.write(f"**Vindhastighet**: {weather_data['wind']['speed']} m/s")
        st.write(f"**Tidpunkt**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.error(
            f"Kunde inte hämta väderdata för {city_name}. Kontrollera stadens namn eller API-nyckeln."
        )


def main():
    st.title("Tidtabell för kollektivtrafik")
    st.write("Visa avgående tåg, bussar eller spårvagnar för en specifik hållplats")

    # Initialize session state variables
    if "origin_id" not in st.session_state:
        st.session_state.origin_id = None
    if "destination_id" not in st.session_state:
        st.session_state.destination_id = None
    if "origin_stops" not in st.session_state:
        st.session_state.origin_stops = []
    if "destination_stops" not in st.session_state:
        st.session_state.destination_stops = []

    # Input for origin and destination (input bars)
    origin_name = st.text_input("Från:", value="Göteborg", key="origin_name")
    destination_name = st.text_input("Till:", value="Malmö", key="destination_name")

    # Button to fetch stops
    if st.button("Sök hållplatser", key="search_stops"):
        resrobot = ResRobot()

        # Fetch origin stops
        if origin_name:
            origin_stops = resrobot.lookup_stop(origin_name)
            if origin_stops:
                st.session_state.origin_stops = origin_stops
            else:
                st.error(f"Inga matchande hållplatser hittades för '{origin_name}'.")
                st.session_state.origin_stops = []

        # Fetch destination stops
        if destination_name:
            destination_stops = resrobot.lookup_stop(destination_name)
            if destination_stops:
                st.session_state.destination_stops = destination_stops
            else:
                st.error(
                    f"Inga matchande hållplatser hittades för '{destination_name}'."
                )
                st.session_state.destination_stops = []

    # Display dropdowns for origin and destination stops
    if st.session_state.origin_stops:
        origin_choice = st.selectbox(
            "Välj ursprungshållplats:",
            [f"{s['name']} (ID: {s['id']})" for s in st.session_state.origin_stops],
            key="origin_choice",
        )
        st.session_state.origin_id = next(
            s["id"]
            for s in st.session_state.origin_stops
            if f"{s['name']} (ID: {s['id']})" == origin_choice
        )

    if st.session_state.destination_stops:
        destination_choice = st.selectbox(
            "Välj destinationshållplats:",
            [
                f"{s['name']} (ID: {s['id']})"
                for s in st.session_state.destination_stops
            ],
            key="destination_choice",
        )
        st.session_state.destination_id = next(
            s["id"]
            for s in st.session_state.destination_stops
            if f"{s['name']} (ID: {s['id']})" == destination_choice
        )

    # Show weather for the default city
    st.header("Väder för standardplats")
    weather_section(DEFAULT_CITY)

    # Map display logic
    if not st.session_state.origin_id or not st.session_state.destination_id:
        st.header("Karta över din resa")
        display_default_map()
    else:
        st.subheader("Uppdaterad Karta över din resa")
        trip_map = TripMap(
            origin_id=st.session_state.origin_id,
            destination_id=st.session_state.destination_id,
        )
        trip_map.display_map()

        # Weather for the destination
        st.header("Väder för destinationen")
        weather_section(destination_name)

        # Fetch schedule when the button is pressed
        if st.button("Hämta tidtabell", key="fetch_schedule"):
            trip_planner = TripPlanner(
                st.session_state.origin_id, st.session_state.destination_id
            )
            trips = trip_planner.trips_for_next_hour()
            if trips:
                st.write("### Resor inom den närmsta timmen:")
                for i, trip in enumerate(trips):
                    trip["time_remaining"] = (
                        trip["depTime"] - pd.Timestamp.now()
                    ).dt.seconds // 60
                    trip_renamed = trip.rename(
                        columns={
                            "name": "Namn",
                            "depTime": "Avgångstid",
                            "arrTime": "Ankomsttid",
                            "time_remaining": "Tid kvar (min)",
                        }
                    )
                    st.write(f"### Resa {i + 1}")
                    st.dataframe(
                        trip_renamed[
                            ["Namn", "Avgångstid", "Ankomsttid", "Tid kvar (min)"]
                        ]
                    )
            else:
                st.write("Inga resor hittades inom den närmsta timmen.")


if __name__ == "__main__":
    main()
