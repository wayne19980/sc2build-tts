from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sc2analyzer.config import SCHEMA  # noqa: E402
from sc2analyzer.migrations import applied_versions, run_migrations  # noqa: E402


def main() -> None:
    applied = run_migrations()
    versions = applied_versions()
    print(f"schema ready: {SCHEMA}")
    print(f"applied this run: {', '.join(applied) if applied else '(none)'}")
    print(f"applied versions: {', '.join(versions)}")


if __name__ == "__main__":
    main()
