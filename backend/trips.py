from datetime import datetime, timedelta

import pandas as pd

from backend.connect_to_api import ResRobot

resrobot = ResRobot()


class TripPlanner:
    def __init__(self, origin_id, destination_id):
        data = resrobot.trips(origin_id, destination_id)
        self.trips = data.get("Trip", []) if data else []
        self.number_trips = len(self.trips)

    def next_available_trip(self):
        t = self.trips[0]
        l = t["LegList"]["Leg"]
        df_legs = pd.DataFrame(l)
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

    def next_available_trips_today(self):
        pass

    def trips_for_next_hour(self):
        now = datetime.now()
        later = now + timedelta(hours=1)
        out = []
        for trip in self.trips:
            l = trip.get("LegList", {}).get("Leg", [])
            if not l:
                continue
            df_legs = pd.DataFrame(l)
            df_stops = pd.json_normalize(
                df_legs["Stops"].dropna(), "Stop", errors="ignore"
            )
            df_stops["depTime"] = pd.to_datetime(
                df_stops["depDate"] + " " + df_stops["depTime"], errors="coerce"
            )
            earliest = df_stops["depTime"].min()
            if earliest and now <= earliest <= later:
                names = []
                for leg in l:
                    names.append(leg.get("name", ""))
                out.append({"label": " -> ".join(names), "df_stops": df_stops})
        return out

    def trips_for_specific_stop(self, stop_name):
        out = []
        for trip in self.trips:
            l = trip["LegList"]["Leg"]
            df_legs = pd.DataFrame(l)
            df_stops = pd.json_normalize(
                df_legs["Stops"].dropna(), "Stop", errors="ignore"
            )
            df_stops["time"] = df_stops["arrTime"].fillna(df_stops["depTime"])
            df_stops["date"] = df_stops["arrDate"].fillna(df_stops["depDate"])
            df_f = df_stops[
                df_stops["name"].str.contains(stop_name, case=False, na=False)
            ]
            if not df_f.empty:
                out.append(df_f)
        return out


if __name__ == "__main__":
    tp = TripPlanner(740000190, 740000191)
    print(tp.trips_for_next_hour())
