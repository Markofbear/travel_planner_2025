import streamlit as st
import pandas as pd
from plot_maps import TripMap
from utils.constants import StationIds
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

st.title("Tidtabell för kommunaltrafik")
st.write("Visa avgående tåg, bussar eller spårvagnar för en specifik hållplats")

origin_id = st.text_input("Ange origin ID (ursprung):", value="740000190")
destination_id = st.text_input("Ange destination ID:", value="740000191")
stop_name = st.text_input("Filtrera på hållplatsens namn (valfritt):", value="")
trip_planner = TripPlanner(origin_id, destination_id)

if st.button("Hämta tidtabell"):
    if stop_name:
        trips = trip_planner.trips_for_specific_stop(stop_name)
    else:
        trips = trip_planner.trips_for_next_hour()

    if trips:
        trip = trips[0]  
        st.write("### Trip 1")

        try:
            leg_count = trip_planner.count_legs(trip["trip"])
            st.write(f"Number of legs: {leg_count}")
        except Exception as e:
            st.write(f"Could not calculate legs for Trip 1: {e}")

        filtered_stops = trip.get("filtered_stops")
        if filtered_stops is not None and not filtered_stops.empty:
            try:
                filtered_stops["time_remaining"] = (
                    pd.to_datetime(filtered_stops["time"]) - pd.Timestamp.now()
                ).dt.seconds // 60
                st.dataframe(
                    filtered_stops[
                        [
                            "name",
                            "time",
                            "date",
                            "depTime",
                            "arrTime",
                            "time_remaining",
                        ]
                    ]
                )
            except Exception as e:
                st.write(f"Error calculating 'time_remaining' for Trip 1: {e}")
        else:
            st.write("No stops found or data is invalid.")
    else:
        st.write("Inga avgångar hittades.")
