"""Fetches weather from WeatherAPI.com and maps it to our schemas.

Responses are cached in memory per location for a few minutes to stay well
within the provider's free-tier limits.
"""

import time

import httpx

from app.config import settings
from app.models import Location
from app.schemas import CurrentWeather, DailyForecast, LocationRead, WeatherResponse
from app.services.weather_codes import icon_for


class WeatherProviderError(Exception):
    """Provider call failed. The message is safe to show to clients (never contains the API key)."""


_cache: dict[tuple[float, float, int], tuple[float, dict]] = {}


async def _fetch(latitude: float, longitude: float, days: int) -> dict:
    cache_key = (round(latitude, 4), round(longitude, 4), days)
    cached = _cache.get(cache_key)
    if cached and time.monotonic() - cached[0] < settings.weather_cache_seconds:
        return cached[1]

    params = {
        "key": settings.weatherapi_key,
        "q": f"{latitude},{longitude}",
        "days": days,
        "aqi": "no",
        "alerts": "no",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(settings.weatherapi_url, params=params)
    except httpx.HTTPError as exc:
        # Don't chain/echo the exception: its text can include the request URL (with the key).
        raise WeatherProviderError(f"Could not reach weather provider ({type(exc).__name__})") from None

    if resp.status_code != 200:
        try:
            message = resp.json()["error"]["message"]
        except (ValueError, KeyError, TypeError):
            message = resp.reason_phrase
        raise WeatherProviderError(f"Weather provider returned {resp.status_code}: {message}")

    data = resp.json()
    _cache[cache_key] = (time.monotonic(), data)
    return data


async def get_weather(location: Location, days: int = settings.forecast_days) -> WeatherResponse:
    data = await _fetch(location.latitude, location.longitude, days)

    cur = data["current"]
    current = CurrentWeather(
        time=cur["last_updated"],
        temperature_c=cur["temp_c"],
        feels_like_c=cur["feelslike_c"],
        humidity_pct=cur["humidity"],
        wind_speed_kmh=cur["wind_kph"],
        weather_code=cur["condition"]["code"],
        description=cur["condition"]["text"].strip(),
        icon=icon_for(cur["condition"]["code"], bool(cur["is_day"])),
    )

    forecast = [
        DailyForecast(
            date=fd["date"],
            temp_max_c=fd["day"]["maxtemp_c"],
            temp_min_c=fd["day"]["mintemp_c"],
            precipitation_probability_pct=fd["day"].get("daily_chance_of_rain"),
            weather_code=fd["day"]["condition"]["code"],
            description=fd["day"]["condition"]["text"].strip(),
            icon=icon_for(fd["day"]["condition"]["code"]),
        )
        for fd in data["forecast"]["forecastday"]
    ]

    return WeatherResponse(location=LocationRead.model_validate(location), current=current, forecast=forecast)
