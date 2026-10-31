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


@st.cache_data(ttl=300, show_spinner=False)
def wake_backend(max_wait: int = 120) -> bool:
    """Poll /health until the backend answers. Render's free plan sleeps idle services
    and a cold start can take ~1 minute, longer than the normal request timeouts.
    Only success is cached (failure raises), so the next rerun retries."""
    deadline = time.monotonic() + max_wait
    while True:
        try:
            if requests.get(f"{BACKEND_URL}/health", timeout=30).ok:
                return True
        except requests.RequestException:
            pass  # still booting (timeout / 502 / 503) - keep trying
        if time.monotonic() >= deadline:
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
