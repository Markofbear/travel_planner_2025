from datetime import datetime

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from backend.connect_to_api import ResRobot, get_weather
from backend.departure_board import DepartureBoard
from backend.trips import TripPlanner

DEFAULT_COORDS = {"lat": 57.7089, "lon": 11.9746}
OPEN_WEATHER_API_KEY = st.secrets["api"]["OPEN_WEATHER_API_KEY"]


@st.cache_data
def fetch_timetable(origin_id, destination_id):
    tp = TripPlanner(origin_id, destination_id)
    return tp.trips_for_next_hour()


def display_default_map():
    folium_map = folium.Map(
        location=[DEFAULT_COORDS["lat"], DEFAULT_COORDS["lon"]], zoom_start=12
    )
    folium.Marker(
        location=[DEFAULT_COORDS["lat"], DEFAULT_COORDS["lon"]], popup="Gothenburg"
    ).add_to(folium_map)
    st_folium(folium_map, width=700, height=500)


def display_map_with_trip(trip):
    if trip:
        stops = trip["df_stops"]
        first_stop = stops.iloc[0]

        folium_map = folium.Map(
            location=[first_stop["lat"], first_stop["lon"]], zoom_start=12
        )

        coordinates = []
        for _, stop in stops.iterrows():
            folium.Marker(
                location=[stop["lat"], stop["lon"]],
                popup=f"{stop['name']} - Avgång: {stop['depTime']}",
            ).add_to(folium_map)
            coordinates.append([stop["lat"], stop["lon"]])

        folium.PolyLine(
            locations=coordinates, color="blue", weight=5, opacity=0.7
        ).add_to(folium_map)

        st.session_state.map_html = folium_map._repr_html_()


def render_map():
    if "map_html" in st.session_state and st.session_state.map_html:
        st.components.v1.html(st.session_state.map_html, height=500)


def weather_section(city_name):
    w = get_weather(city_name, OPEN_WEATHER_API_KEY)
    if w:
        weather_icon_code = w["weather"][0]["icon"]
        weather_icon_url = (
            f"http://openweathermap.org/img/wn/{weather_icon_code}@2x.png"
        )

        st.subheader(f"Vädret i {w['name']}, {w['sys']['country']}")

        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(weather_icon_url, width=100)
        with col2:
            st.write(f"🌡️ {w['main']['temp']}°C")
            st.write(f"💨 {w['wind']['speed']} m/s")
            st.write(f"☁  {w['weather'][0]['description'].capitalize()}")
            st.write(f"💧 {w['main']['humidity']}%")
            st.write(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.error(f"Kunde inte hämta vädret för {city_name}.")


def main():
    st.title("Tidtabell för kollektivtrafik")
    st.write("Visa avgående tåg, bussar eller spårvagnar för en specifik hållplats")

    for key in [
        "origin_id",
        "destination_id",
        "origin_stops",
        "destination_stops",
        "selected_trip",
        "map_html",
    ]:
        if key not in st.session_state:
            st.session_state[key] = None if "id" in key else []

    origin_name = st.text_input("Från:", key="origin_name")
    destination_name = st.text_input("Till:", key="destination_name")

    # Show weather for the selected origin and destination above the map
    if origin_name:
        weather_section(origin_name)
    if destination_name:
        weather_section(destination_name)

    if st.button("🔍 Sök hållplatser", key="search_stops"):
        r = ResRobot()
        if origin_name:
            st.session_state.origin_stops = r.lookup_stop(origin_name) or []
        if destination_name:
            st.session_state.destination_stops = r.lookup_stop(destination_name) or []

    if st.session_state.origin_stops:
        oc = st.selectbox(
            "Välj ursprungshållplats:",
            [f"{s['name']} (ID: {s['id']})" for s in st.session_state.origin_stops],
            key="origin_choice",
        )
        st.session_state.origin_id = next(
            s["id"]
            for s in st.session_state.origin_stops
            if f"{s['name']} (ID: {s['id']})" == oc
        )

    if st.session_state.destination_stops:
        dc = st.selectbox(
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
            if f"{s['name']} (ID: {s['id']})" == dc
        )

    if st.session_state.origin_id and st.session_state.destination_id:
        if st.button("📅 Hämta tidtabell", key="fetch_schedule"):
            st.session_state.timetable = fetch_timetable(
                st.session_state.origin_id, st.session_state.destination_id
            )
            st.session_state.selected_trip = None

        if "timetable" in st.session_state and st.session_state.timetable:
            st.write("### 📅 Välj en resa:")
            for index, t in enumerate(st.session_state.timetable):
                label = t["label"]
                if st.button(label, key=f"trip_{index}"):
                    st.session_state.selected_trip = t
                    display_map_with_trip(t)

        render_map()

        if st.session_state.selected_trip:
            df = st.session_state.selected_trip["df_stops"]
            df["time_remaining"] = (
                df["depTime"] - pd.Timestamp.now()
            ).dt.total_seconds() // 60
            df_renamed = df.rename(
                columns={
                    "name": "Namn",
                    "depTime": "Avgångstid",
                    "arrTime": "Ankomsttid",
                    "time_remaining": "Tid kvar (min)",
                }
            )
            st.write("### Resptabell:")
            st.dataframe(
                df_renamed[["Namn", "Avgångstid", "Ankomsttid", "Tid kvar (min)"]]
            )

    if not st.session_state.origin_id or not st.session_state.destination_id:
        display_default_map()

        st.header("Avgångstavla")
    resrobot = ResRobot()
    departure_board = DepartureBoard(resrobot)
    stop_name = st.text_input("Sök hållplats:", placeholder="Skriv för att söka...")
    if stop_name:
        possible_stops = resrobot.lookup_stop(stop_name)
        if possible_stops:
            selected_stop = st.selectbox(
                "Välj hållplats:",
                [f"{stop['name']} (ID: {stop['id']})" for stop in possible_stops],
                key="selected_stop",
            )
            stop_id = next(
                stop["id"]
                for stop in possible_stops
                if f"{stop['name']} (ID: {stop['id']})" == selected_stop
            )
            if st.button("Visa avgångar"):
                df = departure_board.get_departures_dataframe(stop_id)
                if df is not None:
                    st.write("### Avgångar:")
                    st.dataframe(df, hide_index=True)
                else:
                    st.error("Inga avgångar inom den närmsta timmen hittades.")


if __name__ == "__main__":
    main()
