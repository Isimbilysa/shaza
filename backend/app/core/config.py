"""Settings, read from the environment (see .env.example).

Paths here are anchored to the repository rather than to the current working directory. The
pipeline runs from the repo root and Alembic runs from `backend/`; with a bare relative
`sqlite:///./shaza.db` those two ended up writing to different files, which looks exactly like
"the migration did not work".
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "SHAZA API"
    version: str = "0.1.0"
    environment: str = Field(default="development")

    # PostgreSQL in every environment that has one. Local dev falls back to SQLite so the
    # pipeline runs without Docker -- see docs/decisions/0002-sqlite-for-local-dev.md.
    database_url: str = Field(default="sqlite:///./shaza.db")

    # Comma-separated origins allowed to call the API from a browser.
    cors_origins: str = Field(default="http://localhost:3000")

    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_archive_url: str = "https://archive-api.open-meteo.com/v1/archive"
    http_timeout_seconds: float = 30.0

    @field_validator("database_url")
    @classmethod
    def _anchor_sqlite_path(cls, value: str) -> str:
        """Rewrite a relative SQLite path to an absolute one under `backend/`.

        Leaves Postgres URLs, in-memory SQLite and already-absolute paths alone.
        """
        prefix = "sqlite:///"
        if not value.startswith(prefix):
            return value

        path = value[len(prefix) :]
        if not path or path == ":memory:" or Path(path).is_absolute():
            return value

        resolved = (BACKEND_DIR / path.lstrip("./")).resolve()
        return f"{prefix}{resolved.as_posix()}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith(("postgresql", "postgres://"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
