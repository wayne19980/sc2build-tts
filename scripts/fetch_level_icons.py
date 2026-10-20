from __future__ import annotations

import json
import subprocess
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "vue-app" / "public" / "sc2-icons" / "level"
API = "https://liquipedia.net/starcraft2/api.php"
UA = "sc2build-local/0.1"

FILES: dict[str, str] = {}
for level in (1, 2, 3):
    FILES[f"ProtossGroundWeaponsLevel{level}"] = f"Techtree-upgrade-protoss-groundweaponslevel{level}.png"
    FILES[f"ProtossGroundArmorsLevel{level}"] = f"Techtree-upgrade-protoss-groundarmorlevel{level}.png"
    FILES[f"ProtossPlasmaShieldsLevel{level}"] = f"Techtree-upgrade-protoss-shieldslevel{level}.png"
    FILES[f"ProtossAirWeaponsLevel{level}"] = f"Techtree-upgrade-protoss-airweaponslevel{level}.png"
    FILES[f"ProtossAirArmorsLevel{level}"] = f"Techtree-upgrade-protoss-airarmorlevel{level}.png"
    FILES[f"TerranInfantryWeaponsLevel{level}"] = f"Techtree-upgrade-terran-infantryweaponslevel{level}.png"
    FILES[f"TerranInfantryArmorsLevel{level}"] = f"Techtree-upgrade-terran-infantryarmorlevel{level}.png"
    FILES[f"TerranVehicleWeaponsLevel{level}"] = f"Techtree-upgrade-terran-vehicleweaponslevel{level}.png"
    FILES[f"TerranVehicleArmorsLevel{level}"] = f"Techtree-upgrade-terran-vehicleplatinglevel{level}.png"
    FILES[f"TerranShipWeaponsLevel{level}"] = f"Techtree-upgrade-terran-shipweaponslevel{level}.png"
    FILES[f"TerranShipArmorsLevel{level}"] = f"Techtree-upgrade-terran-shipplatinglevel{level}.png"
    FILES[f"ZergMeleeWeaponsLevel{level}"] = f"Techtree-upgrade-zerg-meleeattacks-level{level}.png"
    FILES[f"ZergMissileWeaponsLevel{level}"] = f"Techtree-upgrade-zerg-missileattacks-level{level}.png"
    FILES[f"ZergGroundArmorsLevel{level}"] = f"Techtree-upgrade-zerg-groundcarapace-level{level}.png"
    FILES[f"ZergFlyerWeaponsLevel{level}"] = f"Techtree-upgrade-zerg-airattacks-level{level}.png"
    FILES[f"ZergFlyerArmorsLevel{level}"] = f"Techtree-upgrade-zerg-flyercarapace-level{level}.png"


def fetch(url: str) -> bytes:
    return subprocess.check_output(["curl", "-sS", "--compressed", "-A", UA, url])


def fetch_json(url: str) -> dict:
    return json.loads(fetch(url).decode("utf-8"))


def fetch_bytes(url: str) -> bytes:
    return fetch(url)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    titles = [f"File:{name}" for name in FILES.values()]
    urls: dict[str, str] = {}
    for start in range(0, len(titles), 40):
        batch = titles[start : start + 40]
        query = urllib.parse.urlencode(
            {
                "action": "query",
                "prop": "imageinfo",
                "iiprop": "url",
                "format": "json",
                "titles": "|".join(batch),
            }
        )
        data = fetch_json(f"{API}?{query}")
        for page in data.get("query", {}).get("pages", {}).values():
            info = page.get("imageinfo") or []
            if info:
                urls[page["title"].removeprefix("File:")] = info[0]["url"]

    missing: list[str] = []
    for key, filename in FILES.items():
        url = urls.get(filename)
        if not url:
            missing.append(filename)
            continue
        target = OUT / f"{key}.png"
        target.write_bytes(fetch_bytes(url))
        print(f"downloaded {key} <- {filename}")

    if missing:
        print("missing:")
        for name in missing:
            print(f"  {name}")


if __name__ == "__main__":
    main()
