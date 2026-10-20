from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAURI_CONF = ROOT / "vue-app" / "src-tauri" / "tauri.conf.json"
BUNDLE = ROOT / "vue-app" / "src-tauri" / "target" / "release" / "bundle" / "nsis"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Tauri static updater manifest")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "latest.json")
    args = parser.parse_args()

    version = json.loads(TAURI_CONF.read_text(encoding="utf-8"))["version"]
    installer = BUNDLE / f"sc2build-tts_{version}_x64-setup.exe"
    if not installer.exists():
        candidates = sorted(BUNDLE.glob("*-setup.exe"))
        print("NSIS files:", ", ".join(p.name for p in candidates) or "(none)")
        if len(candidates) == 1:
            installer = candidates[0]
        else:
            raise FileNotFoundError(f"installer not found: {installer}")
    signature = installer.with_suffix(installer.suffix + ".sig")
    if not signature.exists():
        print("NSIS files:", ", ".join(p.name for p in BUNDLE.glob("*")) or "(none)")
        raise FileNotFoundError(f"signature not found: {signature}")
    print(f"using installer: {installer.name}")
    print(f"using signature: {signature.name}")

    base = args.base_url.rstrip("/")
    payload = {
        "version": version,
        "notes": f"SC2 Build Lab {args.tag}",
        "pub_date": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "platforms": {
            "windows-x86_64": {
                "signature": signature.read_text(encoding="utf-8").strip(),
                "url": f"{base}/{installer.name}",
            }
        },
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} for {installer.name}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"::error::{type(exc).__name__}: {exc}")
        raise
