"""SQLAlchemy engine/session setup for Supabase Postgres."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

url = settings.sqlalchemy_url
connect_args = {}
if url.get_backend_name() == "postgresql":
    # Required for Supabase's transaction pooler (port 6543), harmless elsewhere.
    connect_args["prepare_threshold"] = None

engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
