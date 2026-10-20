from __future__ import annotations

import atexit
import os
from pathlib import Path

import pgserver
from platformdirs import user_data_dir

from . import config

_SERVER = None


def cleanup_database() -> None:
    global _SERVER
    if _SERVER is None:
        return
    try:
        _SERVER.cleanup()
    except Exception:
        pass
    _SERVER = None


atexit.register(cleanup_database)


def _data_root() -> Path:
    configured = os.environ.get("SC2_DATA_DIR", "").strip()
    if configured:
        return Path(configured)
    return Path(user_data_dir("sc2build-tts", appauthor=False))


def ensure_database() -> str:
    """Use an external DATABASE_URL, or start a bundled PostgreSQL server."""
    global _SERVER

    forced = os.environ.get("SC2_EMBEDDED_PG", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    if config.DATABASE_URL and not forced:
        return config.DATABASE_URL

    pgdata = _data_root() / "pgdata"
    pgdata.parent.mkdir(parents=True, exist_ok=True)
    _SERVER = pgserver.get_server(pgdata, cleanup_mode="stop")
    uri = _SERVER.get_uri()

    os.environ["DATABASE_URL"] = uri
    config.DATABASE_URL = uri
    return uri
