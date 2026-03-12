from unittest import TestCase

from app.config import normalize_database_url


class NormalizeDatabaseUrlTests(TestCase):
    def test_keeps_sqlite_urls(self) -> None:
        self.assertEqual(normalize_database_url("sqlite:///./rugsignal.db"), "sqlite:///./rugsignal.db")

    def test_converts_postgres_scheme(self) -> None:
        self.assertEqual(
            normalize_database_url("postgres://user:pass@host:5432/dbname"),
            "postgresql+psycopg://user:pass@host:5432/dbname",
        )

    def test_converts_plain_postgresql_scheme(self) -> None:
        self.assertEqual(
            normalize_database_url("postgresql://user:pass@host:5432/dbname"),
            "postgresql+psycopg://user:pass@host:5432/dbname",
        )

    def test_keeps_explicit_psycopg_driver(self) -> None:
        self.assertEqual(
            normalize_database_url("postgresql+psycopg://user:pass@host:5432/dbname"),
            "postgresql+psycopg://user:pass@host:5432/dbname",
        )
