from backend.connect_to_api import ResRobot
import pandas as pd
from datetime import datetime, timedelta

resrobot = ResRobot()

class TripPlanner:
    def __init__(self, origin_id, destination_id) -> None:
        response = resrobot.trips(origin_id, destination_id)
        self.trips = response.get("Trip") if response else []
        self.number_trips = len(self.trips)

    def next_available_trip(self) -> pd.DataFrame:
        if not self.trips:
            return pd.DataFrame()
        next_trip = self.trips[0]
        leglist = next_trip.get("LegList", {}).get("Leg", [])
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

    def trips_for_next_hour(self) -> list:
        now = datetime.now()
        one_hour_later = now + timedelta(hours=1)
        for trip in self.trips:
            leglist = trip.get("LegList", {}).get("Leg", [])
            df_legs = pd.DataFrame(leglist)
            df_stops = pd.json_normalize(df_legs["Stops"].dropna(), "Stop", errors="ignore")
            df_stops["depTime"] = pd.to_datetime(df_stops["depDate"] + " " + df_stops["depTime"])
            df_stops["time"] = df_stops["arrTime"].fillna(df_stops["depTime"])
            df_stops["date"] = df_stops["arrDate"].fillna(df_stops["depDate"])
            df_filtered = df_stops[
                (df_stops["depTime"] >= now) & (df_stops["depTime"] <= one_hour_later)
            ]
            if not df_filtered.empty:
                return [{"trip": trip, "filtered_stops": df_filtered}]
        return []

    def trips_for_specific_stop(self, stop_name: str) -> list:
        for trip in self.trips:
            leglist = trip.get("LegList", {}).get("Leg", [])
            df_legs = pd.DataFrame(leglist)
            df_stops = pd.json_normalize(df_legs["Stops"].dropna(), "Stop", errors="ignore")
            df_stops["time"] = df_stops["arrTime"].fillna(df_stops["depTime"])
            df_stops["date"] = df_stops["arrDate"].fillna(df_stops["depDate"])
            df_filtered = df_stops[df_stops["name"].str.contains(stop_name, case=False, na=False)]
            if not df_filtered.empty:
                return [{"trip": trip, "filtered_stops": df_filtered}]
        return []

    def count_legs(self, trip):
        leglist = trip.get("LegList", {}).get("Leg", [])
        if isinstance(leglist, list):
            return len(leglist)
        return 0
