from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "services" / "analyzer"
ENTRY = ANALYZER / "run_api.py"
BIN_DIR = ROOT / "vue-app" / "src-tauri" / "binaries"
TARGET = BIN_DIR / "sc2analyzer-api-x86_64-pc-windows-msvc.exe"


def host_triple() -> str:
    try:
        output = subprocess.check_output(["rustc", "-vV"], text=True)
        for line in output.splitlines():
            if line.startswith("host:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return "x86_64-pc-windows-msvc"


def main() -> None:
    if not ENTRY.exists():
        raise SystemExit(f"missing entry point: {ENTRY}")

    BIN_DIR.mkdir(parents=True, exist_ok=True)
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
            "--onefile",
            "--console",
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
            "--hidden-import",
            "psycopg",
            "--add-data",
            f"{ANALYZER / 'sql'}{';' if sys.platform == 'win32' else ':'}sql",
            str(ENTRY),
        ]
        subprocess.run(args, check=True, cwd=ROOT)

        built = dist / "sc2analyzer-api.exe"
        if not built.exists():
            raise SystemExit(f"PyInstaller output not found: {built}")

        target = BIN_DIR / f"sc2analyzer-api-{host_triple()}.exe"
        shutil.copy2(built, target)
        if target != TARGET and TARGET.exists():
            TARGET.unlink()
        print(f"sidecar ready: {target} ({target.stat().st_size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
