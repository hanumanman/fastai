import json
import subprocess


def _run_curl(url: str) -> dict:
    result = subprocess.run(
        ["curl", "-s", url],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed: {result.stderr}")
    return json.loads(result.stdout)


def _geocode(location: str) -> tuple[float, float]:
    encoded = location.replace(" ", "+")
    data = _run_curl(
        f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1"
    )
    if not data.get("results"):
        raise ValueError(f"Location not found: {location}")
    result = data["results"][0]
    return result["latitude"], result["longitude"]


def get_weather(location: str) -> str:
    lat, lon = _geocode(location)
    data = _run_curl(
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
        f"&temperature_unit=celsius"
    )
    current = data["current"]
    temp = current["temperature_2m"]
    humidity = current["relative_humidity_2m"]
    wind = current["wind_speed_10m"]
    code = current["weather_code"]

    weather_map = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    condition = weather_map.get(code, f"Unknown (code {code})")

    return (
        f"Weather in {location}: {condition}, "
        f"{temp}°C, humidity {humidity}%, wind {wind} km/h"
    )
