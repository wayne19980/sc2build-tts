from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "services" / "analyzer"
ENTRY = ANALYZER / "run_api.py"
OUT_DIR = ROOT / "vue-app" / "src-tauri" / "sidecar"
EXE_NAME = "sc2analyzer-api.exe" if sys.platform == "win32" else "sc2analyzer-api"


def main() -> None:
    if not ENTRY.exists():
        raise SystemExit(f"missing entry point: {ENTRY}")

    with tempfile.TemporaryDirectory(prefix="sc2-sidecar-") as temp:
        temp_path = Path(temp)
        dist = temp_path / "dist"
        work = temp_path / "build"
        spec = temp_path / "spec"

        args = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--console",
            "--contents-directory",
            "_internal",
            "--name",
            "sc2analyzer-api",
            "--distpath",
            str(dist),
            "--workpath",
            str(work),
            "--specpath",
            str(spec),
            "--paths",
            str(ANALYZER),
            "--collect-all",
            "sc2reader",
            "--collect-all",
            "spawningtool",
            "--collect-all",
            "fastapi",
            "--collect-all",
            "uvicorn",
            "--collect-all",
            "pgserver",
            "--hidden-import",
            "psycopg",
            "--add-data",
            f"{ANALYZER / 'sql'}{';' if sys.platform == 'win32' else ':'}sql",
            str(ENTRY),
        ]
        subprocess.run(args, check=True, cwd=ROOT)

        built = dist / "sc2analyzer-api"
        if not (built / EXE_NAME).exists():
            raise SystemExit(f"PyInstaller output not found: {built}")

        if OUT_DIR.exists():
            shutil.rmtree(OUT_DIR)
        shutil.copytree(built, OUT_DIR)

        size = sum(path.stat().st_size for path in OUT_DIR.rglob("*") if path.is_file())
        print(f"sidecar ready: {OUT_DIR} ({size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
