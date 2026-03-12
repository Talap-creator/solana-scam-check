from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


settings = get_settings()


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_user_schema_compatibility()

    if settings.admin_bootstrap_email:
        with SessionLocal() as db:
            admin_user = (
                db.query(models.User)
                .filter(models.User.email == settings.admin_bootstrap_email.lower().strip())
                .first()
            )
            if admin_user is not None and admin_user.role != "admin":
                admin_user.role = "admin"
                db.commit()


def ensure_user_schema_compatibility() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "custom_daily_scan_limit" in user_columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN custom_daily_scan_limit INTEGER"))
