"""HTTP client for the FastAPI backend (with Streamlit caching for reads)."""

import os
import time

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


class ApiError(Exception):
    """Backend returned an error; message is the API's `detail`."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def _check(resp: requests.Response) -> None:
    if resp.ok:
        return
    try:
        detail = resp.json().get("detail", resp.text)
    except ValueError:
        detail = resp.text
    if isinstance(detail, list):  # FastAPI validation errors
        detail = "; ".join(
            f"{field}: {d['msg']}" if (field := ".".join(map(str, d["loc"][1:]))) else d["msg"] for d in detail
        )
    raise ApiError(resp.status_code, str(detail))


def _health_ok(resp: requests.Response) -> bool:
    """True only for the real API answer, not Render's HTML 'sleeping'/'suspended' pages."""
    try:
        return resp.status_code == 200 and resp.json().get("status") == "ok"
    except ValueError:
        return False


def backend_is_up(timeout: float = 3) -> bool:
    """One quick, uncached health check."""
    try:
        return _health_ok(requests.get(f"{BACKEND_URL}/health", timeout=timeout))
    except requests.RequestException:
        return False


@st.cache_data(ttl=300, show_spinner=False)
def wake_backend(max_wait: int = 180) -> bool:
    """Poll /health until the backend answers. Render's free plan sleeps idle services
    and a cold start can take ~1 minute, longer than the normal request timeouts.
    Only success is cached (failure raises), so the next rerun retries.
    Each attempt is logged so Render's frontend logs show what came back."""
    start = time.monotonic()
    attempt = 0
    while True:
        attempt += 1
        try:
            # Long read timeout: Render may hold the request while the service boots.
            resp = requests.get(f"{BACKEND_URL}/health", timeout=(5, 60))
            print(
                f"wake_backend attempt={attempt} t={time.monotonic() - start:.1f}s "
                f"status={resp.status_code} x-render-routing={resp.headers.get('x-render-routing')}",
                flush=True,
            )
            if _health_ok(resp):
                return True
        except requests.RequestException as exc:
            print(
                f"wake_backend attempt={attempt} t={time.monotonic() - start:.1f}s error={type(exc).__name__}",
                flush=True,
            )
        if time.monotonic() - start >= max_wait:
            raise TimeoutError(f"Backend at {BACKEND_URL} did not respond within {max_wait}s")
        time.sleep(3)


@st.cache_data(ttl=60)
def fetch_locations() -> list[dict]:
    resp = requests.get(f"{BACKEND_URL}/locations", timeout=10)
    _check(resp)
    return resp.json()


@st.cache_data(ttl=600)
def fetch_weather(location_id: int, days: int = 7) -> dict:
    resp = requests.get(f"{BACKEND_URL}/weather/{location_id}", params={"days": days}, timeout=15)
    _check(resp)
    return resp.json()


def geocode(country: str, city: str, area_name: str, zipcode: str) -> dict:
    params = {"country": country, "city": city, "area_name": area_name, "zipcode": zipcode}
    resp = requests.get(f"{BACKEND_URL}/geocode", params=params, timeout=30)
    _check(resp)
    return resp.json()


def create_location(payload: dict) -> dict:
    resp = requests.post(f"{BACKEND_URL}/locations", json=payload, timeout=30)
    _check(resp)
    fetch_locations.clear()  # so the dropdown shows the new location immediately
    return resp.json()
