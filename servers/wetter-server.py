from mcp.server.fastmcp import FastMCP
from geopy.geocoders import Nominatim
import requests
from datetime import datetime, timedelta

mcp = FastMCP(name="WetterInfoMCP", host="0.0.0.0", port=8055)

def get_coordinates(location: str):
    geolocator = Nominatim(user_agent="wetter_mcp")
    loc = geolocator.geocode(location)
    if not loc:
        raise ValueError(f"Ort nicht gefunden: {location}")
    return loc.latitude, loc.longitude

def get_current_weather(lat: float, lon: float):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true"
    )
    response = requests.get(url)
    response.raise_for_status()
    return response.json().get("current_weather", {})

def get_tomorrow_forecast(lat: float, lon: float):
    tomorrow = (datetime.utcnow() + timedelta(days=1)).date().isoformat()
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        f"&timezone=auto&start_date={tomorrow}&end_date={tomorrow}"
    )
    response = requests.get(url)
    response.raise_for_status()
    daily = response.json().get("daily", {})
    if not daily:
        return {}

    return {
        "date": tomorrow,
        "temp_max": daily["temperature_2m_max"][0],
        "temp_min": daily["temperature_2m_min"][0],
        "precipitation": daily["precipitation_sum"][0]
    }

@mcp.tool()
def get_weather(location: str, forecast: str = "now") -> str:
    """
    Gibt das Wetter für den angegebenen Ort zurück.
    forecast: "now" für aktuelles Wetter, "tomorrow" für die Tagesvorhersage von morgen.
    """
    lat, lon = get_coordinates(location)

    if forecast == "tomorrow":
        data = get_tomorrow_forecast(lat, lon)
        if not data:
            return "Keine Wettervorhersage für morgen gefunden."
        return (
            f"Wettervorhersage für {location} am {data['date']}:\n"
            f"🌤 Max: {data['temp_max']}°C, Min: {data['temp_min']}°C\n"
            f"🌧 Niederschlag: {data['precipitation']} mm"
        )
    else:
        current = get_current_weather(lat, lon)
        if not current:
            return "Keine aktuellen Wetterdaten gefunden."
        return (
            f"Aktuelles Wetter in {location}:\n"
            f"🌡 Temperatur: {current['temperature']}°C\n"
            f"💨 Wind: {current['windspeed']} km/h"
        )

if __name__ == "__main__":
    mcp.run(transport="stdio")