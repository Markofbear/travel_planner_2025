from backend.connect_to_api import ResRobot
import pandas as pd

resrobot = ResRobot()


class TripPlanner:
    """
    A class to interact with Resrobot API to plan trips and retrieve details of available journeys.

    Check explorations to find id for your location

    Attributes:
    ----------
    trips : list
        A list of trips retrieved from the Resrobot API for the specified origin and destination.
    number_trips : int
        The total number of trips available for the specified origin and destination.

    Methods:
    -------
    next_available_trip() -> pd.DataFrame:
        Returns a DataFrame containing details of the next available trip, including stop names,
        coordinates, departure and arrival times, and dates.
    next_available_trips_today() -> list[pd.DataFrame]
        Returns a list of DataFrame objects, where each DataFrame contains similar content as next_available_trip()
    """

    def __init__(self, origin_id, destination_id) -> None:

        self.trips = resrobot.trips(origin_id, destination_id).get("Trip")
        self.number_trips = len(self.trips)

    def next_available_trip(self) -> pd.DataFrame:
        next_trip = self.trips[0]

        leglist = next_trip.get("LegList").get("Leg")

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

    def next_available_trips_today(self) -> list[pd.DataFrame]:
        """Fetches all available trips today between the origin_id and destination_id
        It returns a list of DataFrame objects, where each item corresponds to a trip
        """
        # TODO: implement this method



        

    def trips_for_next_hour(self) -> pd.DataFrame:
        """Filters trips to include only those departing within the next hour."""
        now = datetime.now()
        one_hour_later = now + timedelta(hours=1)
        trips = []

        for trip in self.trips:
            leglist = trip.get("LegList").get("Leg")
            df_legs = pd.DataFrame(leglist)
            df_stops = pd.json_normalize(df_legs["Stops"].dropna(), "Stop", errors="ignore")
            df_stops["depTime"] = pd.to_datetime(df_stops["depDate"] + " " + df_stops["depTime"])
            # Filter trips within the next hour
            df_filtered = df_stops[
                (df_stops["depTime"] >= now) & (df_stops["depTime"] <= one_hour_later)
            ]
            if not df_filtered.empty:
                trips.append(df_filtered)
        return trips

    def trips_for_specific_stop(self, stop_name: str) -> pd.DataFrame:
        """Filters trips to include only those that stop at the specified stop name."""
        trips = []

        for trip in self.trips:
            leglist = trip.get("LegList").get("Leg")
            df_legs = pd.DataFrame(leglist)
            df_stops = pd.json_normalize(df_legs["Stops"].dropna(), "Stop", errors="ignore")
            df_stops["time"] = df_stops["arrTime"].fillna(df_stops["depTime"])
            df_stops["date"] = df_stops["arrDate"].fillna(df_stops["depDate"])
            # Filter trips that stop at the specified stop
            df_filtered = df_stops[df_stops["name"].str.contains(stop_name, case=False, na=False)]
            if not df_filtered.empty:
                trips.append(df_filtered)
        return trips

if __name__ == "__main__":
    data = TripData(
        740000190,
    )
    print(data.next_available_trip()[["arrTime", "depTime", "time", "date"]])
