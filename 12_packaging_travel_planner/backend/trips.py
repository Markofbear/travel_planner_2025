from backend.connect_to_api import ResRobot
from datetime import datetime, timedelta
import pandas as pd


class TripPlanner:
    """
    A class to interact with the ResRobot API to fetch trips and timetables.

    Features:
    ----------
    - Fetch trips between an origin and a destination.
    - Fetch departures for a specific stop.
    - Filter departures by a stop name.
    - Show departures for the next hour.
    - Calculate time left until departure in minutes.

    Methods:
    -------
    next_available_trip(): Fetches the next trip between origin and destination.
    departures_for_stop(): Fetches departures for a specific stop with filtering options.
    """

    def __init__(self):
        self.resrobot = ResRobot()

    def next_available_trip(self, origin_id, destination_id) -> pd.DataFrame:
        """
        Fetches the next available trip between the origin and destination.

        Parameters:
            origin_id (int): The origin stop ID.
            destination_id (int): The destination stop ID.

        Returns:
            pd.DataFrame: A DataFrame containing details of the next available trip.
        """
        # Fetch trips from ResRobot
        response = self.resrobot.trips(origin_id, destination_id)

        if not response or "Trip" not in response:
            raise ValueError(f"No trips found for origin_id={origin_id} and destination_id={destination_id}.")

        trips = response["Trip"]
        next_trip = trips[0]  # Get the first available trip
        leglist = next_trip.get("LegList").get("Leg", [])
        
        # Process the trip data into a DataFrame
        df_legs = pd.DataFrame(leglist)
        df_stops = pd.json_normalize(df_legs["Stops"].dropna(), "Stop", errors="ignore")
        df_stops["time"] = df_stops["arrTime"].fillna(df_stops["depTime"])
        df_stops["date"] = df_stops["arrDate"].fillna(df_stops["depDate"])
        return df_stops[
            [
                "name",
                "extId",
                "lon",
                "lat",
                "depTime",
                "depDate",
                "arrTime",
                "arrDate",
                "time",
                "date",
            ]
        ]

    def departures_for_stop(self, location_id: int, stop_name: str = None) -> pd.DataFrame:
        """
        Fetches departures for a specific stop and filters by stop name (optional).

        Parameters:
            location_id (int): The stop location ID (extId).
            stop_name (str, optional): The stop name to filter departures by.

        Returns:
            pd.DataFrame: A DataFrame containing filtered departure details.
        """

        # Fetch the departure timetable from ResRobot
        raw_data = self.resrobot.timetable_departure(location_id)
        departures = raw_data.get("Departure", [])

        # If there are no departures, return an empty DataFrame
        if not departures:
            return pd.DataFrame(columns=["time_left", "name", "direction", "time", "date", "transportMode"])

        # Convert the raw data into a DataFrame
        df_departures = pd.DataFrame(departures)

        # Combine time and date for proper datetime comparison
        now = datetime.now()
        df_departures["departure_datetime"] = pd.to_datetime(
            df_departures["date"] + " " + df_departures["time"], errors="coerce"
        )

        # Calculate time remaining (in minutes) until departure
        df_departures["time_left"] = (df_departures["departure_datetime"] - now).dt.total_seconds() // 60

        # Filter departures within the next hour
        one_hour_later = now + timedelta(hours=1)
        df_departures = df_departures[
            (df_departures["departure_datetime"] >= now) & (df_departures["departure_datetime"] <= one_hour_later)
        ]

        # Filter by stop name if provided
        if stop_name:
            if "stop" in df_departures.columns:  # Ensure "stop" column exists before filtering
                df_departures = df_departures[df_departures["stop"].str.contains(stop_name, case=False, na=False)]

        # Dynamically check for the existence of required columns
        expected_columns = ["time_left", "name", "direction", "time", "date", "transportMode"]
        available_columns = [col for col in expected_columns if col in df_departures.columns]

        # Return the DataFrame with only available columns
        return df_departures[available_columns]



if __name__ == "__main__":
    # Example usage of the unified TripPlanner class
    trip_planner = TripPlanner()

    # Fetch the next available trip (replace with actual IDs)
    origin_id = 740000001
    destination_id = 740098001

    try:
        next_trip = trip_planner.next_available_trip(origin_id, destination_id)
        print("Next Available Trip:")
        print(next_trip)
    except ValueError as e:
        print(f"Error: {e}")

    # Fetch departures for a specific stop (replace with an actual location_id)
    location_id = 740015565
    stop_name = "Stockholm"  # Optional filter
    departures = trip_planner.departures_for_stop(location_id, stop_name)
    print("Departures for Stop:")
    print(departures)
