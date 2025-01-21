import streamlit as st
import pandas as pd
from plot_maps import TripMap
from utils.constants import StationIds
from backend.connect_to_api import ResRobot

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
st.title("Tidtabell för kommunaltrafik")
st.write("Visa avgående tåg, bussar eller spårvagnar för en specifik hållplats")

origin_id = st.text_input("Ange origin ID (ursprung):", value="740000190")
destination_id = st.text_input("Ange destination ID:", value="740000191")
stop_name = st.text_input("Filtrera på hållplatsens namn (valfritt):", value="")
trip_planner = TripPlanner(origin_id, destination_id)

# Fetch and filter trips
if st.button("Hämta tidtabell"):
    if stop_name:
        trips = trip_planner.trips_for_specific_stop(stop_name)
    else:
        trips = trip_planner.trips_for_next_hour()

    if trips:
        for i, trip in enumerate(trips):
            st.write(f"### Trip {i + 1}")
            trip["time_remaining"] = (pd.to_datetime(trip["time"]) - pd.Timestamp.now()).dt.seconds // 60
            st.dataframe(
                trip[
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
    else:
        st.write("Inga avgångar hittades.")
