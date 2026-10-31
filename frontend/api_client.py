"""HTTP client for the FastAPI backend (with Streamlit caching for reads)."""

import os

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
