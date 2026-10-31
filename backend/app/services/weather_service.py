"""Fetches weather from Open-Meteo and maps it to our schemas."""

import httpx

from app.config import settings
from app.models import Location
from app.schemas import CurrentWeather, DailyForecast, LocationRead, WeatherResponse
from app.services.weather_codes import describe

CURRENT_FIELDS = "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
DAILY_FIELDS = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"


async def get_weather(location: Location, days: int = settings.forecast_days) -> WeatherResponse:
    params = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "current": CURRENT_FIELDS,
        "daily": DAILY_FIELDS,
        "timezone": "auto",
        "forecast_days": days,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(settings.open_meteo_url, params=params)
        resp.raise_for_status()
        data = resp.json()

    cur = data["current"]
    desc, icon = describe(cur["weather_code"])
    current = CurrentWeather(
        time=cur["time"],
        temperature_c=cur["temperature_2m"],
        feels_like_c=cur["apparent_temperature"],
        humidity_pct=cur["relative_humidity_2m"],
        wind_speed_kmh=cur["wind_speed_10m"],
        weather_code=cur["weather_code"],
        description=desc,
        icon=icon,
    )

    daily = data["daily"]
    forecast = []
    for i, day in enumerate(daily["time"]):
        code = daily["weather_code"][i]
        d_desc, d_icon = describe(code)
        forecast.append(
            DailyForecast(
                date=day,
                temp_max_c=daily["temperature_2m_max"][i],
                temp_min_c=daily["temperature_2m_min"][i],
                precipitation_probability_pct=daily["precipitation_probability_max"][i],
                weather_code=code,
                description=d_desc,
                icon=d_icon,
            )
        )

    return WeatherResponse(location=LocationRead.model_validate(location), current=current, forecast=forecast)
