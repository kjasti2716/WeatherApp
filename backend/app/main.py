from fastapi import FastAPI

from app.routers import geocode, locations, weather

app = FastAPI(title="Weather API", version="0.1.0")
app.include_router(locations.router)
app.include_router(weather.router)
app.include_router(geocode.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
