"""Address -> coordinates using OpenStreetMap Nominatim (free, no API key).

Tries progressively broader queries so we still get a usable point when the
exact area isn't in OSM, and reports which level matched.
"""

import httpx

from app.config import settings
from app.schemas import GeocodeResult, LocationAddress


def _search(client: httpx.Client, params: dict) -> dict | None:
    resp = client.get(settings.nominatim_url, params={**params, "format": "jsonv2", "limit": 1})
    resp.raise_for_status()
    results = resp.json()
    return results[0] if results else None


def geocode(address: LocationAddress) -> GeocodeResult | None:
    a = address
    attempts: list[tuple[str, dict]] = [
        ("area", {"q": f"{a.area_name}, {a.city}, {a.zipcode}, {a.country}"}),
        ("area", {"q": f"{a.area_name}, {a.city}, {a.country}"}),
        ("postcode", {"postalcode": a.zipcode, "country": a.country}),
        ("city", {"city": a.city, "country": a.country}),
    ]
    headers = {"User-Agent": settings.geocoder_user_agent}
    with httpx.Client(timeout=10, headers=headers) as client:
        for match, params in attempts:
            hit = _search(client, params)
            if hit:
                return GeocodeResult(
                    latitude=float(hit["lat"]),
                    longitude=float(hit["lon"]),
                    display_name=hit["display_name"],
                    match=match,
                )
    return None
