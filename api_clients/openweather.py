import os
import requests

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

load_dotenv()

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

US_COUNTRY_VALUES = {
    "us",
    "usa",
    "u.s.",
    "u.s.a.",
    "united states",
    "united states of america",
}


def _normalize_country(country: str) -> str:
    cleaned = country.strip()

    if not cleaned:
        return "US"

    lowered = cleaned.lower()
    if lowered in US_COUNTRY_VALUES:
        return "US"

    if len(cleaned) == 2:
        return cleaned.upper()

    return cleaned


def fetch_weather_context(city: str, state: str = "", country: str = "US") -> dict:
    """
    Fetch current weather by city/state/country.

    Note: OpenWeather recommends lat/lon for best accuracy, but city-based
    lookup is enough for our MVP and easier to demo.
    """
    if not OPENWEATHER_API_KEY:
        return {
            "source": "OpenWeather",
            "status": "skipped",
            "reason": "Missing OPENWEATHER_API_KEY",
        }

    if not city:
        return {
            "source": "OpenWeather",
            "status": "skipped",
            "reason": "Missing city",
        }

    normalized_country = _normalize_country(country)

    location_parts = [city]

    if state:
        location_parts.append(state)

    if normalized_country:
        location_parts.append(normalized_country)

    location_query = ",".join(location_parts)

    params = {
        "q": location_query,
        "appid": OPENWEATHER_API_KEY,
        "units": "imperial",
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()

        weather_items = payload.get("weather", [])
        main_weather = weather_items[0] if weather_items else {}

        main = payload.get("main", {})
        wind = payload.get("wind", {})

        return {
            "source": "OpenWeather",
            "status": "success",
            "location_query": location_query,
            "city": payload.get("name"),
            "country": payload.get("sys", {}).get("country", normalized_country),
            "condition": main_weather.get("main"),
            "description": main_weather.get("description"),
            "temperature_f": main.get("temp"),
            "feels_like_f": main.get("feels_like"),
            "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"),
            "raw": {
                "coord": payload.get("coord"),
                "weather": weather_items,
                "main": main,
                "wind": wind,
            },
        }

    except requests.RequestException as exc:
        return {
            "source": "OpenWeather",
            "status": "error",
            "location_query": location_query,
            "error": str(exc),
        }
