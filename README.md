# Weather App

FastAPI backend + Streamlit frontend, with locations stored in **Supabase (PostgreSQL)**.
Pick a location from the dropdown to see current weather and a multi-day forecast.
Weather data comes from [Open-Meteo](https://open-meteo.com/); coordinates for new locations are looked up
automatically with [OpenStreetMap Nominatim](https://nominatim.org/). Both are free and need no API key.

## Structure

```
WeatherApp/
├── backend/
│   ├── .env.example                # copy to .env and set DATABASE_URL
│   └── app/
│       ├── main.py                 # FastAPI app + routers
│       ├── config.py               # settings (pydantic-settings, reads .env)
│       ├── database.py             # SQLAlchemy engine/session
│       ├── models.py               # ORM: Location
│       ├── schemas.py              # Pydantic request/response models
│       ├── crud.py                 # location DB operations
│       ├── routers/
│       │   ├── locations.py        # CRUD /locations
│       │   ├── geocode.py          # GET /geocode (address -> lat/long)
│       │   └── weather.py          # GET /weather/{location_id}?days=7
│       └── services/
│           ├── weather_service.py  # Open-Meteo client + mapping
│           ├── geocoding_service.py # Nominatim client
│           └── weather_codes.py    # WMO code -> description/icon
├── frontend/
│   ├── app.py                      # entry point + page navigation
│   ├── api_client.py               # backend calls (+ caching)
│   └── views/
│       ├── weather.py              # dropdown, current, forecast
│       └── add_location.py         # address form -> auto lat/long -> save
├── db/
│   └── schema.sql                  # locations table (run in Supabase SQL Editor)
└── requirements.txt
```

## Database setup (Supabase)

1. Create a project at https://supabase.com.
2. In **SQL Editor**, run `db/schema.sql`.
3. **Project → Connect** → copy the *Session pooler* URI into `backend/.env`:
   ```bash
   cp backend/.env.example backend/.env   # then edit DATABASE_URL
   ```
   Use the `postgresql+psycopg://` scheme and your database password.
4. Start the app and add locations on the **Add location** page (or via `POST /locations`).

RLS is enabled on `locations` with no policies, so the public anon key can't read or write it;
the backend connects as `postgres` and isn't affected.

## Setup & run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cd backend && uvicorn app.main:app --reload       # http://localhost:8000/docs
cd frontend && streamlit run app.py               # http://localhost:8501
```

## Locations API

| Method | Path                    | Purpose                      |
|--------|-------------------------|------------------------------|
| GET    | `/locations`            | List all                     |
| GET    | `/locations/{id}`       | Get one                      |
| POST   | `/locations`            | Create; lat/long optional (geocoded if omitted). 409 if country+city+area exists |
| PATCH  | `/locations/{id}`       | Partial update               |
| DELETE | `/locations/{id}`       | Delete                       |
| GET    | `/weather/{id}?days=7`  | Current + forecast for a location |
| GET    | `/geocode?country=&city=&area_name=&zipcode=` | Look up coordinates (preview) |

### Location fields

| Field       | Type   | Notes                                  |
|-------------|--------|----------------------------------------|
| `country`   | text   | e.g. India                             |
| `city`      | text   | e.g. Hyderabad                         |
| `area_name` | text   | e.g. Kondapur — unique per city+country |
| `zipcode`   | text   | text to keep leading zeros / letters   |
| `latitude`  | float  | -90 … 90                               |
| `longitude` | float  | -180 … 180                             |

Example:
```bash
curl -X POST localhost:8000/locations -H 'Content-Type: application/json' -d \
  '{"country":"India","city":"Hyderabad","area_name":"Madhapur","zipcode":"500081"}'
```

## Deploy (Render)

`render.yaml` defines two free web services: `weatherapp-api` (FastAPI) and `weatherapp-ui` (Streamlit).

1. Push to GitHub, then in Render: **New → Blueprint** → select this repo → **Apply**.
2. Enter the secrets when prompted:
   - `DATABASE_URL`: Supabase **session pooler** URI without the password (Render is IPv4-only; the direct `db.<ref>.supabase.co` host won't connect)
   - `DB_PASSWORD`: database password
   - `BACKEND_URL`: `https://weatherapp-api.onrender.com` (check the API service's actual URL and update if different)
3. Check `https://<api-url>/health` returns `{"status":"ok"}`, then open the UI service URL.

Free services sleep after 15 minutes idle; the first request afterwards takes ~30–60 s.
