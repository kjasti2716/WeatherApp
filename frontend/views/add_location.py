"""Add a location: user enters the address, coordinates are looked up automatically."""

import pandas as pd
import requests
import streamlit as st

from api_client import ApiError, create_location, fetch_locations, geocode

MATCH_NOTES = {
    "area": None,
    "postcode": "Exact area not found on the map; coordinates are for the zipcode.",
    "city": "Area and zipcode not found on the map; coordinates are for the city centre.",
}

st.title("📍 Add location")

if flash := st.session_state.pop("flash", None):
    st.success(flash)

with st.form("address"):
    col1, col2 = st.columns(2)
    country = col1.text_input("Country", value="India")
    city = col2.text_input("City", placeholder="Hyderabad")
    area_name = col1.text_input("Area name", placeholder="Kondapur")
    zipcode = col2.text_input("Zipcode", placeholder="500084")
    find = st.form_submit_button("Find coordinates", type="primary")

address = {
    "country": country.strip(),
    "city": city.strip(),
    "area_name": area_name.strip(),
    "zipcode": zipcode.strip(),
}

if find:
    st.session_state.pop("candidate", None)
    missing = [k.replace("_", " ") for k, v in address.items() if not v]
    if missing:
        st.warning(f"Please fill in: {', '.join(missing)}")
    else:
        with st.spinner("Looking up coordinates…"):
            try:
                st.session_state.candidate = {"address": address, "point": geocode(**address)}
            except ApiError as exc:
                st.error(str(exc))
            except requests.RequestException as exc:
                st.error(f"Could not reach the backend: {exc}")

candidate = st.session_state.get("candidate")
# Drop a stale lookup if the user edited the address afterwards.
if candidate and candidate["address"] != address:
    st.session_state.pop("candidate")
    candidate = None

if candidate:
    point = candidate["point"]
    st.subheader("Coordinates")
    c1, c2 = st.columns(2)
    c1.metric("Latitude", f"{point['latitude']:.5f}")
    c2.metric("Longitude", f"{point['longitude']:.5f}")
    st.caption(point["display_name"])
    if note := MATCH_NOTES[point["match"]]:
        st.warning(note)
    st.map(pd.DataFrame([{"lat": point["latitude"], "lon": point["longitude"]}]), zoom=13)

    if st.button("Save location", type="primary"):
        payload = {**address, "latitude": point["latitude"], "longitude": point["longitude"]}
        try:
            saved = create_location(payload)
        except ApiError as exc:
            st.error(str(exc))
        except requests.RequestException as exc:
            st.error(f"Could not reach the backend: {exc}")
        else:
            st.session_state.pop("candidate")
            st.session_state.flash = f"Saved {saved['area_name']}, {saved['city']}."
            st.rerun()

st.divider()
st.subheader("Saved locations")
try:
    locations = fetch_locations()
except (ApiError, requests.RequestException) as exc:
    st.error(f"Failed to load locations: {exc}")
else:
    if locations:
        st.dataframe(
            pd.DataFrame(locations)[["area_name", "city", "country", "zipcode", "latitude", "longitude"]].rename(
                columns=lambda c: c.replace("_", " ").title()
            ),
            hide_index=True,
            width="stretch",
        )
    else:
        st.caption("None yet.")
