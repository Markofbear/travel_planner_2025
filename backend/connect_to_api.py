import os

import requests
from dotenv import load_dotenv

load_dotenv()


class ResRobot:
    API_KEY = os.getenv("API_KEY")

    def trips(self, origin_id=740000001, destination_id=740098001):
        """origing_id and destination_id can be found from Stop lookup API"""
        url = f"https://api.resrobot.se/v2.1/trip?format=json&originId={origin_id}&destId={destination_id}&passlist=true&showPassingPoints=true&accessId={self.API_KEY}"  # noqa: E501

        try:
            response = requests.get(url)
            response.raise_for_status()

            return response.json()
        except requests.exceptions.RequestException as err:
            print(f"Network or HTTP error: {err}")

    def access_id_from_location(self, location):
        url = f"https://api.resrobot.se/v2.1/location.name?input={location}&format=json&accessId={self.API_KEY}"
        response = requests.get(url)
        result = response.json()

        print(f"{'Name':<50} extId")

        for stop in result.get("stopLocationOrCoordLocation"):
            stop_data = next(iter(stop.values()))

            # returns None if extId doesn't exist
            if stop_data.get("extId"):
                print(f"{stop_data['name']:<50} {stop_data['extId']}")

    def timetable_departure(self, location_id=740015565):
        url = f"https://api.resrobot.se/v2.1/departureBoard?id={location_id}&format=json&accessId={self.API_KEY}"
        response = requests.get(url)
        result = response.json()
        return result

    def timetable_arrival(self, location_id=740015565):
        url = f"https://api.resrobot.se/v2.1/arrivalBoard?id={location_id}&format=json&accessId={self.API_KEY}"
        response = requests.get(url)
        result = response.json()
        return result

    def lookup_stop(self, stop_name: str) -> list:
        """Search for stops based on the stop name using fuzzy matching."""
        url = "https://api.resrobot.se/v2.1/location.name"
        params = {
            "input": f"{stop_name}?",  # Frågetecknet läggs här för fuzzy matching
            "format": "json",  # Tvinga API:et att returnera JSON
            "accessId": self.API_KEY,
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            # Kontrollera efter stopLocationOrCoordLocation
            if "stopLocationOrCoordLocation" in data:
                stop_locations = data["stopLocationOrCoordLocation"]
                results = []
                for location in stop_locations:
                    # Iterera över både StopLocation och CoordLocation
                    if "StopLocation" in location:
                        stop = location["StopLocation"]
                        results.append(
                            {
                                "name": stop["name"],
                                "id": stop["extId"],
                                "lon": stop["lon"],
                                "lat": stop["lat"],
                            }
                        )
                    elif "CoordLocation" in location:
                        coord = location["CoordLocation"]
                        results.append(
                            {
                                "name": coord["name"],
                                "id": coord["id"],
                                "lon": coord["lon"],
                                "lat": coord["lat"],
                            }
                        )
                return results
            else:
                print(f"Inga hållplatser hittades för '{stop_name}'.")
                return []
        except requests.exceptions.RequestException as e:
            print(f"API-fel: {e}")
            return []


def get_weather(city_name, OPEN_WEATHER_API_KEY):
    """
    Fetches the current weather data for a given city using the OpenWeatherMap API.

    Parameters:
        city_name (str): The name of the city.
        api_key (str): OpenWeatherMap API key.

    Returns:
        dict: A dictionary containing weather data if successful, otherwise None.
    """
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&units=metric&appid={OPEN_WEATHER_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None


# resrobot = ResRobot()

# pprint(resrobot.timetable_arrival()["Arrival"][0])
