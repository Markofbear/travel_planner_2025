from datetime import datetime

import folium
import pandas as pd
import streamlit as st

from backend.connect_to_api import ResRobot, get_weather
from backend.departure_board import DepartureBoard
from backend.trips import TripPlanner

DEFAULT_COORDS = {"lat": 57.7089, "lon": 11.9746}
OPEN_WEATHER_API_KEY = st.secrets["api"]["OPEN_WEATHER_API_KEY"]

st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://images.pexels.com/photos/2203416/pexels-photo-2203416.jpeg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }
    [data-testid="stAppViewContainer"] {
        background-color: rgba(0, 0, 0, 0.8) !important;
        padding: 2rem;
        border-radius: 1rem;
        margin: 2rem auto;
        border: 2px solid #fff;
        max-width: 900px;
    }
    [data-testid="stMarkdownContainer"] {
        color: #fff;
    }
    div.stButton > button {
        background-color: black !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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
    st.session_state.map_html = folium_map._repr_html_()


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


def home_tab():
    st.title("Trafikapp")
    st.write(
        "Välkommen till vårt grupparbete för en väl fungerande trafikapp! Vi som har jobbat på den är Anna, Björn och Brian"
    )
    st.image(
        "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTdlZDVmeG1ueDZyb2k5eGNwYXNnaWp3dnY3OHJ2ajlkYzY3M3FzMCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/13HgwGsXF0aiGY/giphy.gif",
        width=800,
    )


def tidtabell_tab():
    for key in [
        "origin_id",
        "destination_id",
        "origin_stops",
        "destination_stops",
        "selected_trip",
        "map_html",
        "timetable",
    ]:
        if key not in st.session_state:
            st.session_state[key] = (
                None
                if key in ["origin_id", "destination_id", "timetable", "selected_trip"]
                else []
            )
    if not st.session_state.map_html:
        display_default_map()
    origin_name = st.text_input("Från:", key="origin_name")
    destination_name = st.text_input("Till:", key="destination_name")
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
        selected_origin = st.selectbox(
            "Välj ursprungshållplats:",
            st.session_state.origin_stops,
            format_func=lambda s: s["name"],
            key="origin_choice",
        )
        st.session_state.origin_id = selected_origin["id"]
    if st.session_state.destination_stops:
        selected_destination = st.selectbox(
            "Välj destinationshållplats:",
            st.session_state.destination_stops,
            format_func=lambda s: s["name"],
            key="destination_choice",
        )
        st.session_state.destination_id = selected_destination["id"]
    if st.session_state.origin_id and st.session_state.destination_id:
        if st.button("📅 Hämta tidtabell", key="fetch_schedule"):
            st.session_state.timetable = fetch_timetable(
                st.session_state.origin_id, st.session_state.destination_id
            )
            st.session_state.selected_trip = None
        if st.session_state.timetable:
            st.write("### 📅 Välj en resa:")
            for index, t in enumerate(st.session_state.timetable):
                label = t["label"]
                if st.button(label, key=f"trip_{index}"):
                    st.session_state.selected_trip = t
                    display_map_with_trip(t)
    render_map()

    if st.session_state.selected_trip:
        trip_label = st.session_state.selected_trip.get("label", "")
        transport_list = [segment.strip() for segment in trip_label.split("->")]

        # Count unique transport changes
        num_transfers = max(len(set(transport_list)) - 1, 0)
        st.write(f"🚏 **Antal byten:** {num_transfers}")

        # ✅ Define df before using it!
        df = st.session_state.selected_trip["df_stops"].copy()

        df["depTime"] = pd.to_datetime(df["depTime"], errors="coerce")
        df["arrTime"] = pd.to_datetime(df["arrTime"], errors="coerce")
        df["time_remaining"] = (
            df["depTime"] - pd.Timestamp.now()
        ).dt.total_seconds() // 60
        df.loc[df["time_remaining"] < 0, "time_remaining"] = (
            0  # Ensure no negative times
        )
        df["depTime"] = df["depTime"].dt.strftime("%H:%M")
        df["arrTime"] = df["arrTime"].dt.strftime("%H:%M")

        df_renamed = df.rename(
            columns={
                "name": "Namn",
                "depTime": "Avgångstid",
                "arrTime": "Ankomsttid",
                "time_remaining": "Tid kvar (min)",
            }
        )

        # ✅ Count the number of stops
        num_stops = max(len(df_renamed) - 1, 0)

        st.write(
            f"🛑 **Antal stopp på vägen:** {num_stops}"
        )  # ✅ New line to display the stop count

        st.write("### Restabell:")
        st.dataframe(df_renamed[["Namn", "Avgångstid", "Ankomsttid", "Tid kvar (min)"]])


def avgangstavla_tab():
    resrobot = ResRobot()
    departure_board = DepartureBoard(resrobot)
    stop_name = st.text_input(
        "Sök hållplats:", placeholder="Skriv för att söka...", key="dep_stop_name"
    )
    if stop_name:
        possible_stops = resrobot.lookup_stop(stop_name)

        if possible_stops:
            selected_stop = st.selectbox(
                "Välj hållplats:",
                possible_stops,
                format_func=lambda stop: stop["name"],
                key="selected_stop_departure",
            )

            if selected_stop:
                stop_id = selected_stop["id"]

                if st.button("Visa avgångar", key="show_departures"):
                    df = departure_board.get_departures_dataframe(stop_id)

                    if df is not None:
                        st.write("### Avgångar:")
                        # CSS to left-align column names
                        st.markdown(
                            """
                            <style>
                                th {
                                    text-align: left !important;
                                }
                                td {
                                    text-align: left !important;
                                }
                            </style>
                            """,
                            unsafe_allow_html=True,
                        )

                        # Add icons
                        df["Typ"] = df["Typ"].apply(
                            lambda x: departure_board.map_transport_icon(x) + " " + x
                        )

                        # Show table with HTML
                        st.markdown(
                            df.to_html(escape=False, index=False),
                            unsafe_allow_html=True,
                        )
                    else:
                        st.error("Inga avgångar inom den närmsta timmen hittades.")
            else:
                st.error("Ingen hållplats valdes. Välj en från listan.")
        else:
            st.error(f"Inga matchande hållplatser hittades för '{stop_name}'.")


def weather_tab():
    st.title("Väder")
    city = st.text_input("Ange stad:")
    if city:
        weather_section(city)


def main():
    tabs = st.tabs(["Hem", "Tidtabell", "Avgångstavla", "Väder"])
    with tabs[0]:
        home_tab()
    with tabs[1]:
        tidtabell_tab()
    with tabs[2]:
        avgangstavla_tab()
    with tabs[3]:
        weather_tab()


if __name__ == "__main__":
    main()
