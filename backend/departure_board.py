import pandas as pd


class DepartureBoard:
    """
    A class to handle the a departure board for public transport.
    """

    def __init__(self, api_client):
        self.api_client = api_client

    def get_departures(self, stop_id):
        # Fetch departures from the API for a given stop ID
        data = self.api_client.timetable_departure(stop_id)
        departures = data.get("Departure", [])

        structured_departures = []

        # Loop through each raw departure entry to structure the data
        for departure in departures:
            time = departure.get("time")
            date = departure.get("date")
            direction = departure.get("direction")
            transport_type = departure.get("ProductAtStop", {}).get(
                "catOutL", "Unknown"
            )
            line_number = departure.get("ProductAtStop", {}).get("displayNumber", "N/A")

            departure_time = pd.to_datetime(f"{date} {time}")
            current_time = pd.Timestamp.now()
            minutes_to_departure = (departure_time - current_time).total_seconds() // 60

            structured_departures.append(
                {
                    "time": time,
                    "date": date,
                    "direction": direction,
                    "transport_type": transport_type,
                    "line_number": line_number,
                    "minutes_to_departure": int(minutes_to_departure),
                }
            )

        return structured_departures

    # Filter departures to include only those within 60 minutes
    def filter_departures(self, departures, max_minutes=60):
        return [
            departure
            for departure in departures
            if 0 <= departure["minutes_to_departure"] <= max_minutes
        ]
