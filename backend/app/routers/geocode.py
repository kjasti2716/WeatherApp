import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas import GeocodeResult, LocationAddress
from app.services.geocoding_service import geocode

router = APIRouter(prefix="/geocode", tags=["geocode"])


def geocode_or_raise(address: LocationAddress) -> GeocodeResult:
    try:
        result = geocode(address)
    except httpx.HTTPError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Geocoding provider error: {exc}") from exc
    if result is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Could not find coordinates for this address")
    return result


@router.get("", response_model=GeocodeResult)
def geocode_address(address: LocationAddress = Depends()):
    """Look up coordinates for country/city/area_name/zipcode (preview before saving)."""
    return geocode_or_raise(address)
