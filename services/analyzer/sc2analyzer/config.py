from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]


def _env_candidates() -> list[Path]:
    candidates: list[Path] = []
    explicit = os.environ.get("SC2_ENV_FILE")
    if explicit:
        candidates.append(Path(explicit))
    candidates.append(Path.cwd() / ".env")
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.extend([exe_dir / ".env", exe_dir.parent / ".env"])
    candidates.append(REPO_ROOT / ".env")
    # When bundled, __file__ lives in the temporary extraction directory.
    candidates.extend(parent / ".env" for parent in Path(__file__).resolve().parents[:6])
    return candidates


for _candidate in _env_candidates():
    if _candidate.is_file():
        load_dotenv(_candidate, override=False)
        break

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
SCHEMA = os.environ.get("SC2_SCHEMA", "sc2build").strip() or "sc2build"


def sqlalchemy_url() -> str:
    """Return a SQLAlchemy URL that uses the installed psycopg 3 driver."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set in .env")

    parts = urlsplit(DATABASE_URL)
    scheme = parts.scheme
    if scheme in {"postgres", "postgresql"}:
        scheme = "postgresql+psycopg"
    elif scheme == "postgresql+psycopg2":
        scheme = "postgresql+psycopg"

    return urlunsplit((scheme, parts.netloc, parts.path, parts.query, parts.fragment))
