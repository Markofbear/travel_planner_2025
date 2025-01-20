import streamlit as st
from plot_maps import TripMap
from utils.constants import StationIds

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
