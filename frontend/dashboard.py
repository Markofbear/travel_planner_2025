import streamlit as st
import pandas as pd
from plot_maps import TripMap
from utils.constants import StationIds
from backend.connect_to_api import ResRobot
from backend.trips import TripPlanner


trip_map = TripMap(
    origin_id=StationIds.MALMO.value, destination_id=StationIds.UMEA.value
)


def main():
    st.markdown("# Reseplanerare")
    st.markdown(
        "Den här dashboarden syftar till att både utforska data för olika platser, men ska även fungera som en reseplanerare där du får välja och planera din resa."
    )

    trip_map.display_map()

if __name__ == "__main__":
    main()

# Initialize the TripPlanner
st.title("Tidtabell för kollektivtrafik")
st.write("Visa avgående tåg, bussar eller spårvagnar för en specifik hållplats")

origin_name = st.text_input("Ange namn för ursprungshållplats:", value="Göteborg", key="origin_name")
destination_name = st.text_input("Ange namn för destinationshållplats:", value="Malmö", key="destination_name")

if st.button("Sök hållplatser"):
    resrobot = ResRobot()

    origin_stops = resrobot.lookup_stop(origin_name)
    destination_stops = resrobot.lookup_stop(destination_name)

    # Save stop options to session state
    if origin_stops:
        st.session_state.origin_stops = origin_stops
    else:
        st.error("Inga matchande hållplatser hittades för ursprungshållplatsen.")
        st.session_state.origin_stops = []

    if destination_stops:
        st.session_state.destination_stops = destination_stops
    else:
        st.error("Inga matchande hållplatser hittades för destinationshållplatsen.")
        st.session_state.destination_stops = []

# Dropdown for selecting origin stop
if "origin_stops" in st.session_state and st.session_state.origin_stops:
    origin_choice = st.selectbox(
        "Välj ursprungshållplats:",
        [f"{s['name']} (ID: {s['id']})" for s in st.session_state.origin_stops],
        key="origin_choice",
    )
    st.session_state.origin_id = next(
        s["id"] for s in st.session_state.origin_stops if f"{s['name']} (ID: {s['id']})" == origin_choice
    )

# Dropdown for selecting destination stop
if "destination_stops" in st.session_state and st.session_state.destination_stops:
    destination_choice = st.selectbox(
        "Välj destinationshållplats:",
        [f"{s['name']} (ID: {s['id']})" for s in st.session_state.destination_stops],
        key="destination_choice",
    )
    st.session_state.destination_id = next(
        s["id"] for s in st.session_state.destination_stops if f"{s['name']} (ID: {s['id']})" == destination_choice
    )

# Display the selected stops and their IDs
if "origin_id" in st.session_state and "destination_id" in st.session_state:
    st.write(f"Valt ursprung-ID: {st.session_state.origin_id}")
    st.write(f"Valt destinations-ID: {st.session_state.destination_id}")

    # Fetch and display trips for the next hour
    if st.button("Hämta tidtabell"):
        trip_planner = TripPlanner(st.session_state.origin_id, st.session_state.destination_id)
        trips = trip_planner.trips_for_next_hour()  # Använder metoden för nästa timme

        if trips:
            st.write("### Resor inom den närmsta timmen:")
            for i, trip in enumerate(trips):
                trip["time_remaining"] = (trip["depTime"] - pd.Timestamp.now()).dt.seconds // 60
                st.write(f"### Resa {i + 1}")
                st.dataframe(
                    trip[
                        ["name", "depTime", "arrTime", "time_remaining"]
                    ]
                )
        else:
            st.write("Inga resor hittades inom den närmsta timmen.")





