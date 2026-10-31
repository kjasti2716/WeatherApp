"""Pydantic request/response schemas."""

from datetime import date, datetime

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---- Locations ----
class LocationAddress(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    country: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    area_name: str = Field(min_length=1, max_length=100)
    zipcode: str = Field(min_length=1, max_length=20)


class LocationCreate(LocationAddress):
    """Coordinates are optional: if omitted, the backend geocodes the address."""

    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def both_or_neither(self) -> Self:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Provide both latitude and longitude, or neither")
        return self


class LocationUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    country: str | None = Field(default=None, min_length=1, max_length=100)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    area_name: str | None = Field(default=None, min_length=1, max_length=100)
    zipcode: str | None = Field(default=None, min_length=1, max_length=20)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class LocationRead(LocationAddress):
    model_config = ConfigDict(from_attributes=True)

    id: int
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: datetime


# ---- Geocoding ----
class GeocodeResult(BaseModel):
    latitude: float
    longitude: float
    display_name: str
    # How precise the match is: the area itself, only the zipcode, or only the city.
    match: Literal["area", "postcode", "city"]


# ---- Weather ----
class CurrentWeather(BaseModel):
    time: datetime
    temperature_c: float
    feels_like_c: float
    humidity_pct: int
    wind_speed_kmh: float
    weather_code: int
    description: str
    icon: str


class DailyForecast(BaseModel):
    date: date
    temp_max_c: float
    temp_min_c: float
    precipitation_probability_pct: int | None
    weather_code: int
    description: str
    icon: str


class WeatherResponse(BaseModel):
    location: LocationRead
    current: CurrentWeather
    forecast: list[DailyForecast]
