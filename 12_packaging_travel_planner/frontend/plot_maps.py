import folium
import streamlit as st
from backend.trips import TripPlanner
from abc import ABC, abstractmethod
import pandas as pd


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


class TripMap(Maps):
    """
    TripMap handles the visualization of trips on a map.

    Attributes:
    -----------
    origin_id : int
        The ID of the origin station.
    destination_id : int
        The ID of the destination station.
    trip_planner : TripPlanner
        Instance of the TripPlanner class used to fetch trip data.
    next_trip : pd.DataFrame
        DataFrame containing the details of the next available trip.

    Methods:
    --------
    _create_map():
        Creates a Folium map for the trip.
    display_map():
        Displays the trip map using Streamlit.
    """

    def __init__(self, origin_id, destination_id):
        self.origin_id = origin_id
        self.destination_id = destination_id
        self.trip_planner = TripPlanner()  # No origin_id or destination_id passed to the constructor
        self.next_trip = self._fetch_next_trip()

    def _fetch_next_trip(self):
        """
        Fetches the next available trip between the origin and destination.

        Returns:
        --------
        pd.DataFrame:
            DataFrame containing details of the next available trip.
        """
        try:
            return self.trip_planner.next_available_trip(self.origin_id, self.destination_id)
        except ValueError as e:
            st.error(f"Ett fel inträffade: {e}")
            return pd.DataFrame()

    def _create_map(self):
        """
        Creates a Folium map for the next trip.

        Returns:
        --------
        folium.Map:
            A Folium map object displaying the trip.
        """
        if self.next_trip.empty:
            return folium.Map(location=[56.046467, 12.694512], zoom_start=5)  # Default to Malmö location

        # Create the map centered on the mean location of stops in the trip
        geographical_map = folium.Map(
            location=[self.next_trip["lat"].mean(), self.next_trip["lon"].mean()],
            zoom_start=5,
        )

        # Add markers for each stop in the trip
        for _, row in self.next_trip.iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=f"""
                    <b>{row['name']}</b><br>
                    Avgångstid: {row['time']}<br>
                    Datum: {row['date']}
                """,
            ).add_to(geographical_map)

        return geographical_map

    def display_map(self):
        """
        Displays the trip map using Streamlit.

        If no trip data is available, displays an error message.
        """
        st.markdown("## Karta över stationerna i din resa")
        st.markdown("Klicka på varje station för mer information. Detta är en exempelresa.")

        # Check if trip data is available
        if self.next_trip.empty:
            st.warning("Ingen resa hittades mellan den angivna ursprungs- och destinationshållplatsen.")
        else:
            # Display the map using Streamlit's HTML embedding
            st.components.v1.html(self._create_map()._repr_html_(), height=500)
