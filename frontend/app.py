"""Streamlit entry point: `streamlit run app.py`."""

import json

import streamlit as st
import streamlit.components.v1 as components

from api_client import BACKEND_URL, backend_is_up, wake_backend

st.set_page_config(page_title="Weather App", page_icon="🌤️", layout="centered")

# Render free services sleep when idle; wake the backend before any page calls it.
if not backend_is_up():
    # Requests from this (Render-hosted) server may not wake a sleeping Render service,
    # but a request from the user's browser does, so fire one from the browser too.
    # no-cors: we only need the request sent, not to read the reply.
    components.html(
        f"<script>fetch({json.dumps(BACKEND_URL + '/health')}, {{mode: 'no-cors', cache: 'no-store'}});</script>",
        height=0,
    )
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
