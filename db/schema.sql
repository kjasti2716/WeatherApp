-- Locations shown in the WeatherApp dropdown.
create table if not exists public.locations (
    id          bigint generated always as identity primary key,
    country     text             not null,
    city        text             not null,
    area_name   text             not null,
    zipcode     text             not null,  -- text: keeps leading zeros / alphanumeric codes
    latitude    double precision not null check (latitude  between -90  and 90),
    longitude   double precision not null check (longitude between -180 and 180),
    created_at  timestamptz      not null default now(),
    updated_at  timestamptz      not null default now(),
    constraint locations_country_city_area_key unique (country, city, area_name)
);

create index if not exists locations_zipcode_idx on public.locations (zipcode);

-- The FastAPI backend connects as the postgres role, which bypasses RLS.
-- Enabling RLS with no policies keeps the table closed to the public anon/authenticated API keys.
alter table public.locations enable row level security;
