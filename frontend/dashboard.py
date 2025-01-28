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

DEFAULT_COORDS = {"lat": 57.7089, "lon": 11.9746}
DEFAULT_CITY = "Göteborg"
load_dotenv()
OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")


def display_default_map():
    folium_map = folium.Map(
        location=[DEFAULT_COORDS["lat"], DEFAULT_COORDS["lon"]], zoom_start=12
    )
    folium.Marker(
        location=[DEFAULT_COORDS["lat"], DEFAULT_COORDS["lon"]], popup="Gothenburg"
    ).add_to(folium_map)
    st_folium(folium_map, width=700, height=500)


def weather_section(city_name):
    if not OPEN_WEATHER_API_KEY:
        st.error("Ingen API-nyckel hittades.")
        return
    w = get_weather(city_name, OPEN_WEATHER_API_KEY)
    if w:
        st.subheader(f"Vädret i {w['name']}, {w['sys']['country']}")
        st.write(f"Temperatur: {w['main']['temp']}°C")
        st.write(f"Känns som: {w['main']['feels_like']}°C")
        st.write(f"Väder: {w['weather'][0]['description'].capitalize()}")
        st.write(f"Luftfuktighet: {w['main']['humidity']}%")
        st.write(f"Vindhastighet: {w['wind']['speed']} m/s")
        st.write(f"Tidpunkt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.error(f"Kunde inte hämta väderdata för {city_name}.")


def main():
    st.title("Tidtabell för kollektivtrafik")
    st.write("Visa avgående tåg, bussar eller spårvagnar för en specifik hållplats")
    if "origin_id" not in st.session_state:
        st.session_state.origin_id = None
    if "destination_id" not in st.session_state:
        st.session_state.destination_id = None
    if "origin_stops" not in st.session_state:
        st.session_state.origin_stops = []
    if "destination_stops" not in st.session_state:
        st.session_state.destination_stops = []
    origin_name = st.text_input("Från:", value="Göteborg", key="origin_name")
    destination_name = st.text_input("Till:", value="Malmö", key="destination_name")
    if st.button("Sök hållplatser", key="search_stops"):
        r = ResRobot()
        if origin_name:
            o_stops = r.lookup_stop(origin_name)
            if o_stops:
                st.session_state.origin_stops = o_stops
            else:
                st.error(f"Inga matchande hållplatser hittades för '{origin_name}'.")
                st.session_state.origin_stops = []
        if destination_name:
            d_stops = r.lookup_stop(destination_name)
            if d_stops:
                st.session_state.destination_stops = d_stops
            else:
                st.error(
                    f"Inga matchande hållplatser hittades för '{destination_name}'."
                )
                st.session_state.destination_stops = []
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
    st.header("Väder för standardplats")
    weather_section(DEFAULT_CITY)
    if not st.session_state.origin_id or not st.session_state.destination_id:
        st.header("Karta över din resa")
        display_default_map()
    else:
        st.subheader("Uppdaterad Karta över din resa")
        trip_map = TripMap(st.session_state.origin_id, st.session_state.destination_id)
        trip_map.display_map()
        st.header("Väder för destinationen")
        weather_section(destination_name)
        if st.button("Hämta tidtabell", key="fetch_schedule"):
            tp = TripPlanner(
                st.session_state.origin_id, st.session_state.destination_id
            )
            trips = tp.trips_for_next_hour()
            if trips:
                st.write("Resor inom den närmsta timmen:")
                for t in trips:
                    label = t["label"]
                    df = t["df_stops"]
                    df["time_remaining"] = (
                        df["depTime"] - pd.Timestamp.now()
                    ).dt.seconds // 60
                    df_renamed = df.rename(
                        columns={
                            "name": "Namn",
                            "depTime": "Avgångstid",
                            "arrTime": "Ankomsttid",
                            "time_remaining": "Tid kvar (min)",
                        }
                    )
                    earliest = df["depTime"].min()
                    diff = (earliest - pd.Timestamp.now()).total_seconds() // 60
                    st.write(f"{label} - avgår om {int(diff)} min")
                    st.dataframe(
                        df_renamed[
                            ["Namn", "Avgångstid", "Ankomsttid", "Tid kvar (min)"]
                        ]
                    )
            else:
                st.write("Inga resor hittades inom den närmsta timmen.")


if __name__ == "__main__":
    main()
