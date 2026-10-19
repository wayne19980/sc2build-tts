from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sc2analyzer.db import SessionLocal  # noqa: E402
from sc2analyzer.importer import import_folder, import_replay  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Import SC2 replays into PostgreSQL")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--folder", type=Path, help="Import every .SC2Replay under this folder")
    source.add_argument("--replay", type=Path, help="Import one replay")
    parser.add_argument("--group-folder", type=Path, help="Folder bucket to store a single replay under")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        if args.folder:
            result = import_folder(session, args.folder)
        else:
            result = import_replay(session, args.replay, args.group_folder)
    finally:
        session.close()

    print(f"folder: {result.folder_path} (id={result.folder_id})")
    print(f"imported: {len(result.imported)}")
    for path in result.imported:
        print(f"  + {path}")
    print(f"skipped: {len(result.skipped)}")
    for path in result.skipped:
        print(f"  = {path}")
    print(f"errors: {len(result.errors)}")
    for error in result.errors:
        print(f"  ! {error.file}: {error.message}")


if __name__ == "__main__":
    main()
