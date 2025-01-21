import streamlit as st
import pandas as pd
from plot_maps import TripMap
from utils.constants import StationIds
from backend.connect_to_api import ResRobot
from backend.trips import TripPlanner


# Initialize TripMap for displaying the map
trip_map = TripMap(
    origin_id=StationIds.MALMO.value, destination_id=StationIds.UMEA.value
)

# Main dashboard function
def main():
    # Header for the dashboard
    st.markdown("# Reseplanerare")
    st.markdown(
        "Den här dashboarden syftar till att både utforska data för olika platser, men ska även fungera som en reseplanerare där du får välja och planera din resa."
    )

    # Display the map
    trip_map.display_map()

    # Initialize the TripPlanner functionality
    st.title("Tidtabell för kommunaltrafik")
    st.write("Visa avgående tåg, bussar eller spårvagnar för en specifik hållplats.")

    # Inputs for the timetable functionality
    location_id = st.text_input("Ange hållplatsens ID (extId):", value="740015565")
    stop_name = st.text_input("Filtrera på hållplatsens namn (valfritt):", value="")
    origin_id = st.text_input("Ange origin ID (ursprung):", value="740000190")
    destination_id = st.text_input("Ange destination ID:", value="740000191")

    # Create a TripPlanner instance
    trip_planner = TripPlanner()

    # Fetch and display trips (next hour or filtered by stop)
    if st.button("Hämta tidtabell"):
        try:
            if location_id:
                # Fetch departures for a specific stop
                st.write("### Tidtabell för hållplats")
                departures = trip_planner.departures_for_stop(int(location_id), stop_name)

                # If departures exist, show the data
                if not departures.empty:
                    departures["time_left"] = departures["time_left"].astype(int)
                    st.write("### Avgångar inom en timme:")
                    st.dataframe(departures)

                    # Highlight departures leaving soon
                    st.write("### Avgångar som snart lämnar (<10 minuter):")
                    leaving_soon = departures[departures["time_left"] < 10]
                    if not leaving_soon.empty:
                        st.dataframe(leaving_soon)
                    else:
                        st.write("Inga avgångar inom 10 minuter.")
                else:
                    st.write("Inga avgångar hittades för denna hållplats.")

            # Fetch the next available trip between the origin and destination
            st.write("### Nästa tillgängliga resa")
            next_trip = trip_planner.next_available_trip(int(origin_id), int(destination_id))
            st.write("Detaljer för nästa resa:")
            st.dataframe(next_trip)
        except ValueError as e:
            st.error(f"Ett fel inträffade: {e}")


if __name__ == "__main__":
    main()
