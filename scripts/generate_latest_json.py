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
    signature = installer.with_suffix(installer.suffix + ".sig")
    if not installer.exists():
        raise SystemExit(f"installer not found: {installer}")
    if not signature.exists():
        raise SystemExit(f"signature not found: {signature}")

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
    main()
