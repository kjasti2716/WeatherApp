"""Streamlit entry point: `streamlit run app.py`."""

import streamlit as st

st.set_page_config(page_title="Weather App", page_icon="🌤️", layout="centered")

pages = st.navigation(
    [
        st.Page("views/weather.py", title="Weather", icon="🌤️", default=True),
        st.Page("views/add_location.py", title="Add location", icon="📍"),
    ]
)
pages.run()
