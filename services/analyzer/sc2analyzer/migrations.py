from __future__ import annotations

import hashlib
import re
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .config import SCHEMA
from .db import engine as default_engine

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "sql" / "migrations"
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_LOCK_KEY = 0x5C2B01D


def _validate_schema(schema: str) -> None:
    if not _IDENTIFIER.match(schema):
        raise ValueError(f"invalid schema name: {schema!r}")


def migration_files() -> list[Path]:
    files = sorted(MIGRATIONS_DIR.glob("*.sql"), key=lambda path: path.name)
    if not files:
        raise RuntimeError(f"no migrations found in {MIGRATIONS_DIR}")
    return files


def run_migrations(
    engine: Engine | None = None,
    schema: str = SCHEMA,
) -> list[str]:
    """Apply pending SQL migrations and return the versions applied."""
    _validate_schema(schema)
    engine = engine or default_engine
    applied: list[str] = []

    with engine.begin() as connection:
        # Serialize startup across API workers / Tauri sidecar instances.
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _LOCK_KEY})
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        connection.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS "{schema}".schema_migrations (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )

        for path in migration_files():
            version = path.name.split("_", 1)[0]
            raw_sql = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(raw_sql.encode("utf-8")).hexdigest()

            row = connection.execute(
                text(
                    f'SELECT checksum FROM "{schema}".schema_migrations '
                    "WHERE version = :version"
                ),
                {"version": version},
            ).first()

            if row is not None:
                if row[0] != checksum:
                    raise RuntimeError(
                        f"migration {path.name} changed after it was applied; "
                        "add a new migration instead"
                    )
                continue

            sql = raw_sql.replace("{{schema}}", schema)
            connection.exec_driver_sql(sql)
            connection.execute(
                text(
                    f'INSERT INTO "{schema}".schema_migrations '
                    "(version, name, checksum) VALUES (:version, :name, :checksum)"
                ),
                {"version": version, "name": path.name, "checksum": checksum},
            )
            applied.append(version)

    return applied


def applied_versions(engine: Engine | None = None, schema: str = SCHEMA) -> list[str]:
    _validate_schema(schema)
    engine = engine or default_engine
    with engine.connect() as connection:
        table = connection.execute(
            text("SELECT to_regclass(:name)"), {"name": f"{schema}.schema_migrations"}
        ).scalar()
        if not table:
            return []
        return list(
            connection.execute(
                text(f'SELECT version FROM "{schema}".schema_migrations ORDER BY version')
            ).scalars()
        )
