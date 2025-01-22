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
        
        all_stops = []
        for leg in leglist:
            stops = pd.json_normalize(leg["Stops"], "Stop", errors="ignore")
            stops["time"] = stops["arrTime"].fillna(stops["depTime"])
            stops["date"] = stops["arrDate"].fillna(stops["depDate"])
            stops["leg_name"] = leg.get("name", "")
            all_stops.append(stops)

        full_trip = pd.concat(all_stops, ignore_index=True)

        return full_trip[
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
                "leg_name",
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

    def count_stops(self, trip):
        """
        Counts the total number of stops in the given trip by aggregating all stops from each leg.
        """
        leglist = trip.get("LegList", {}).get("Leg", [])
        total_stops = 0

        for leg in leglist:
            stops = pd.json_normalize(leg["Stops"], "Stop", errors="ignore")
            total_stops += len(stops)

        return total_stops
