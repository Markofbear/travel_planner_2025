import folium
import streamlit as st
from streamlit_folium import st_folium

from backend.trips import TripPlanner


class TripMap:
    def __init__(self, origin_id, destination_id):
        trip_planner = TripPlanner(origin_id, destination_id)
        self.next_trip = trip_planner.next_available_trip()

    def _create_map(self):
        if self.next_trip.empty:
            st.error("No data available for the next trip. Cannot create map.")
            return None

        if not all(col in self.next_trip.columns for col in ["lat", "lon"]):
            st.error("Missing latitude or longitude data for the trip.")
            return None

        map_center = [self.next_trip["lat"].iloc[0], self.next_trip["lon"].iloc[0]]
        geographical_map = folium.Map(location=map_center, zoom_start=12)

        coordinates = self.next_trip[["lat", "lon"]].dropna().values.tolist()

        for _, row in self.next_trip.iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=f"{row['name']}<br>{row['time']}<br>{row['date']}",
            ).add_to(geographical_map)

        if len(coordinates) > 1:
            folium.PolyLine(coordinates, color="blue", weight=5, opacity=0.7).add_to(
                geographical_map
            )

        return geographical_map

    def display_map(self):
        st.markdown("## Karta över stationerna i din resa")
        st.markdown("Klicka på varje station för mer information.")
        folium_map = self._create_map()

        if folium_map is not None:
            st_folium(folium_map)
        else:
            st.error("Failed to create the map. Please check the trip data.")
