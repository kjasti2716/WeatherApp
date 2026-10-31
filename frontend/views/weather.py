from datetime import date

import pandas as pd
import requests
import streamlit as st

from api_client import BACKEND_URL, ApiError, fetch_locations, fetch_weather


def label(loc: dict) -> str:
    return f"{loc['area_name']}, {loc['city']}"


st.title("🌤️ Weather App")

try:
    locations = fetch_locations()
except requests.RequestException as exc:
    st.error(f"Could not reach the backend at {BACKEND_URL}. Is FastAPI running?\n\n{exc}")
    st.stop()
except ApiError as exc:
    st.error(f"Failed to load locations: {exc}")
    st.stop()

if not locations:
    st.info("No locations yet. Add one to get started.")
    st.page_link("views/add_location.py", label="Add location", icon="📍")
    st.stop()

selected = st.selectbox("Location", locations, format_func=label)
days = st.slider("Forecast days", min_value=3, max_value=14, value=7)

try:
    data = fetch_weather(selected["id"], days)
except (requests.RequestException, ApiError) as exc:
    st.error(f"Failed to load weather: {exc}")
    st.stop()

# --- Current weather ---
cur = data["current"]
loc = data["location"]
st.subheader(f"Now in {label(loc)}")
st.caption(f"{loc['country']} · PIN {loc['zipcode']} · {loc['latitude']:.4f}, {loc['longitude']:.4f}")
st.markdown(f"### {cur['icon']} {cur['description']}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Temperature", f"{cur['temperature_c']:.1f} °C")
c2.metric("Feels like", f"{cur['feels_like_c']:.1f} °C")
c3.metric("Humidity", f"{cur['humidity_pct']} %")
c4.metric("Wind", f"{cur['wind_speed_kmh']:.0f} km/h")
st.caption(f"Updated {cur['time'].replace('T', ' ')} (local time)")

# --- Forecast ---
st.subheader(f"{days}-day forecast")
df = pd.DataFrame(data["forecast"])
df["date"] = pd.to_datetime(df["date"])
df["Day"] = df["date"].apply(lambda d: "Today" if d.date() == date.today() else d.strftime("%a %d %b"))

cols = st.columns(min(len(df), 7))
for i, row in df.head(7).iterrows():
    with cols[i]:
        st.markdown(f"**{row['Day']}**")
        st.markdown(f"<div style='font-size:2rem'>{row['icon']}</div>", unsafe_allow_html=True)
        st.write(f"{row['temp_max_c']:.0f}° / {row['temp_min_c']:.0f}°")
        if pd.notna(row["precipitation_probability_pct"]):
            st.caption(f"💧 {int(row['precipitation_probability_pct'])}%")

st.line_chart(
    df.set_index("date")[["temp_max_c", "temp_min_c"]].rename(columns={"temp_max_c": "Max °C", "temp_min_c": "Min °C"})
)

with st.expander("Forecast table"):
    st.dataframe(
        df[["Day", "description", "temp_max_c", "temp_min_c", "precipitation_probability_pct"]].rename(
            columns={
                "description": "Conditions",
                "temp_max_c": "Max °C",
                "temp_min_c": "Min °C",
                "precipitation_probability_pct": "Rain %",
            }
        ),
        hide_index=True,
        width="stretch",
    )
