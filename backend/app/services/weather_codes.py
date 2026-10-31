"""WeatherAPI.com condition codes -> emoji. Descriptions come from the API itself.

Full list: https://www.weatherapi.com/docs/weather_conditions.json
"""

_GROUPS: list[tuple[str, set[int]]] = [
    ("☁️", {1006, 1009}),
    ("⛅", {1003}),
    ("🌫️", {1030, 1135, 1147}),
    ("🌦️", {1063, 1150, 1153, 1180, 1183, 1240}),
    ("🌧️", {1072, 1168, 1171, 1186, 1189, 1192, 1195, 1198, 1201, 1243, 1246}),
    ("🌨️", {1066, 1069, 1114, 1117, 1204, 1207, 1210, 1213, 1216, 1219, 1222, 1225,
            1237, 1249, 1252, 1255, 1258, 1261, 1264}),
    ("⛈️", {1087, 1273, 1276, 1279, 1282}),
]
ICONS: dict[int, str] = {code: icon for icon, codes in _GROUPS for code in codes}


def icon_for(code: int, is_day: bool = True) -> str:
    if code == 1000:  # Sunny / Clear
        return "☀️" if is_day else "🌙"
    return ICONS.get(code, "🌡️")
