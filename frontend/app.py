"""Streamlit entry point: `streamlit run app.py`."""

import streamlit as st

from api_client import BACKEND_URL, wake_backend

st.set_page_config(page_title="Weather App", page_icon="🌤️", layout="centered")

# Render free services sleep when idle; wake the backend before any page calls it.
try:
    with st.spinner("Waking up the backend (first load after idle can take up to a minute)…"):
        wake_backend()
except TimeoutError as exc:
    st.error(f"{exc}. Please refresh in a moment.")
    st.stop()

pages = st.navigation(
    [
        st.Page("views/weather.py", title="Weather", icon="🌤️", default=True),
        st.Page("views/add_location.py", title="Add location", icon="📍"),
    ]
)
pages.run()
