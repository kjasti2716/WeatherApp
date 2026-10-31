"""Application settings, loaded from environment variables / backend/.env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL, make_url

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    # Connection URL *without* the password, e.g. postgresql://postgres@db.<ref>.supabase.co:5432/postgres
    database_url: str
    # Kept separate so special characters (@, :, /, #) don't break URL parsing.
    db_password: str | None = None

    # WeatherAPI.com (free key: https://www.weatherapi.com/signup.aspx). Free plan returns up to 3 forecast days.
    weatherapi_key: str
    weatherapi_url: str = "https://api.weatherapi.com/v1/forecast.json"
    forecast_days: int = 3
    weather_cache_seconds: int = 600
    nominatim_url: str = "https://nominatim.openstreetmap.org/search"
    # Nominatim policy requires an identifying User-Agent (https://operations.osmfoundation.org/policies/nominatim/)
    geocoder_user_agent: str = "WeatherApp/0.1 (learning project)"

    @property
    def sqlalchemy_url(self) -> URL:
        raw = self.database_url
        # Accept the URL exactly as Supabase shows it; use the psycopg (v3) driver.
        for prefix in ("postgres://", "postgresql://"):
            if raw.startswith(prefix):
                raw = "postgresql+psycopg://" + raw[len(prefix):]
        url = make_url(raw)
        if self.db_password:
            url = url.set(password=self.db_password)
        return url


settings = Settings()
