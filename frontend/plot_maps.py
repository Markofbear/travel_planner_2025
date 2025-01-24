from abc import ABC, abstractmethod

import folium
import streamlit as st
from streamlit_folium import st_folium

from backend.trips import TripPlanner


class Maps(ABC):
    """
    Abstract base class for map-related operations.

    Methods:
    --------
    display_map():
        Abstract method to display a map. Must be implemented by subclasses.
    """

    @abstractmethod
    def display_map(self):
        """
        Abstract method to display a map.

        Subclasses must provide an implementation for this method.
        """
        raise NotImplementedError


# class TripMap(Maps):
#     def __init__(self, origin_id, destination_id):
#         trip_planner = TripPlanner(origin_id, destination_id)
#         self.next_trip = trip_planner.next_available_trip()

#     def _create_map(self):
#         geographical_map = folium.Map(
#             location=[self.next_trip["lat"].mean(), self.next_trip["lon"].mean()],
#             zoom_start=5,
#         )

#         for _, row in self.next_trip.iterrows():
#             folium.Marker(
#                 location=[row["lat"], row["lon"]],
#                 popup=f"{row['name']}<br>{row['time']}<br>{row['date']}",
#             ).add_to(geographical_map)

#         return geographical_map

#     def display_map(self):
#         st.markdown("## Karta över stationerna i din resa")
#         st.markdown(
#             "Klicka på varje station för mer information. Detta är en exempelresa mellan Malmö och Umeå"
#         )
#         st.components.v1.html(self._create_map()._repr_html_(), height=500)


class TripMap:
    def __init__(self, origin_id, destination_id):
        # Initialize TripPlanner and fetch the next available trip
        trip_planner = TripPlanner(origin_id, destination_id)
        self.next_trip = trip_planner.next_available_trip()

    def _create_map(self):
        # Validate data
        if self.next_trip.empty:
            st.error("No data available for the next trip. Cannot create map.")
            return None

        if not all(col in self.next_trip.columns for col in ["lat", "lon"]):
            st.error("Missing latitude or longitude data for the trip.")
            return None

        # Create a Folium map centered on the first stop (or fallback to default)
        map_center = [self.next_trip["lat"].iloc[0], self.next_trip["lon"].iloc[0]]
        geographical_map = folium.Map(location=map_center, zoom_start=12)

        # Add markers for each stop
        for _, row in self.next_trip.iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=f"{row['name']}<br>{row['time']}<br>{row['date']}",
            ).add_to(geographical_map)

        return geographical_map

    def display_map(self):
        # Render the map
        st.markdown("## Karta över stationerna i din resa")
        st.markdown("Klicka på varje station för mer information.")
        folium_map = self._create_map()

        if folium_map is not None:
            # Use streamlit-folium to display the map
            st_folium(folium_map)
        else:
            st.error("Failed to create the map. Please check the trip data.")
