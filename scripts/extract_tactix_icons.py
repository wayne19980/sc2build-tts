from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

DEFAULT_ZIP = Path(r"D:\Program Files\TactiX_1.2.3\Mods\StarCraft II Mod.zip")
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "vue-app" / "public" / "sc2-icons"


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract TactiX SC2 unit icons")
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.out.exists() and args.force:
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True, exist_ok=True)

    copied = 0
    with zipfile.ZipFile(args.zip) as archive:
        for name in archive.namelist():
            if not name.startswith("icons/") or not name.lower().endswith(".png"):
                continue
            target = args.out / Path(name).name
            target.write_bytes(archive.read(name))
            copied += 1

    print(f"extracted {copied} icons -> {args.out}")


if __name__ == "__main__":
    main()
