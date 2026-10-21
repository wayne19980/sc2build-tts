# SC2 Build Analysis

Local StarCraft II replay analysis app: import a folder of `.SC2Replay` files, extract tech/building/unit events, and visualize build orders on a tech tree.

## Layout

- `services/analyzer/` - Python backend, PostgreSQL, replay parsing, migrations
- `vue-app/` - Vue 3 frontend (legacy Pyodide flow still present; migrating to backend API)
- `index.html` - legacy standalone frontend
- `test/` - sample replay used by tests

## Commands

Create/refresh the local environment:

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r services/analyzer/requirements.txt
```

Database migrations and import:

```bash
.venv/Scripts/python.exe services/analyzer/scripts/init_db.py
.venv/Scripts/python.exe services/analyzer/scripts/import_folder.py --folder test
```

Run the API (migrations run automatically at startup):

```bash
.venv/Scripts/python.exe -m sc2analyzer.api
```

Run the Vue app against the local API:

```bash
pnpm dev
```

The frontend reads `VITE_API_BASE` and defaults to `http://127.0.0.1:8765`.
Run the backend from `services/analyzer` or set `PYTHONPATH=services/analyzer`.

Tests:

```bash
cd services/analyzer
../../.venv/Scripts/python.exe -m pytest -q
```

Tauri desktop shell (starts the backend automatically):

```bash
pnpm tauri:dev
```

In debug mode Tauri spawns the API from the repo `.venv`. For a release build,
package the sidecar first:

```bash
.venv/Scripts/python.exe scripts/build_sidecar.py
cd vue-app
pnpm tauri:build
```

The release sidecar is built as a PyInstaller `--onedir` bundle into
`src-tauri/sidecar/` and bundled as a Tauri resource (generated, not committed).

## Release

- `.github/workflows/release.yml` builds Windows installers and uploads them
  as workflow artifacts.
- Pushing a `v*` tag also publishes the installers to a GitHub Release.
- The workflow builds the Python sidecar first and then runs `pnpm tauri:build`.
- The old VPS deploy workflow has been removed.

## Tauri / Overlay

- Main window is a normal desktop window (`main`).
- `overlay` is created on demand as transparent, always-on-top, skip-taskbar,
  non-focusable and click-through.
- Overlay state is sent from the main window through the `sc2-overlay-state`
  Tauri event; the overlay requests the initial state with `sc2-overlay-ready`.
- Native directory selection uses `@tauri-apps/plugin-dialog`.
- Overlay only works over windowed / borderless-fullscreen SC2, not exclusive fullscreen.
- `Ctrl+Shift+O` toggles the overlay globally; the main window also has an
  overlay button, opacity slider and position presets. Enabling the overlay also
  starts the voice reader; disabling it stops the voice reader.
- The UI has a global Chinese/English switch; it also drives voice language and
  overlay/build/unit display names.
- The overlay is a compact 760x220 transparent window, not full-screen.
  It shows a build ticker and a mini tech tree of all future unlocks; timestamps
  within 60 seconds are highlighted.
- The backend is spawned from Rust (`tauri-plugin-shell`): `.venv` Python in
  debug uses external PostgreSQL from `.env`; release uses the bundled sidecar
  with embedded PostgreSQL via `pgserver`, no `.env` required.
- The sidecar watchdog stops the embedded PostgreSQL when the app exits.
- Auto-update uses the Tauri updater. The public key is in `tauri.conf.json`;
  the private key is kept outside the repo at `~/.tauri/sc2build-tts.key`.
  Add its contents as the `TAURI_SIGNING_PRIVATE_KEY` GitHub secret.
- Update endpoints point to gh-proxy and then GitHub. Release CI generates
  `latest.json` only when the signing key secret is configured.

## Database

- PostgreSQL connection comes from root `.env` -> `DATABASE_URL`.
- All application objects live in the `sc2build` schema, never `public`.
- `SC2_SCHEMA` can override the schema name.
- Migrations are ordered SQL files in `services/analyzer/sql/migrations/`.

### Migration rules

- Never edit an applied migration; add the next numbered file instead.
- The runner stores versions/checksums in `sc2build.schema_migrations`.
- The API runs pending migrations on startup.
- Migration SQL uses `{{schema}}` placeholders; the runner replaces them.
- Keep SQLAlchemy models in `sc2analyzer/models.py` in sync with migrations.

## Data conventions

- `t_sec` is the in-game display time: `frame / frames_per_second` (22.4 on Faster).
- `events.kind` values:
  - `order` - build-order command timestamp from spawningtool
  - `build_start` / `build_done` - building lifecycle
  - `unit_training_start` - warp-in start
  - `unit_born` - actual unit birth (including warp-in and Archon merge completion)
  - `unit_died`, `unit_morph`, `upgrade_done`, `ability`
- `units` stores one lifecycle row per unit for cumulative production and alive-at-time queries.
- Folder imports hash files first, skip existing games without parsing, then parse/insert new
  replays in parallel worker processes. `SC2_IMPORT_WORKERS` overrides the worker count
  (defaults to half the logical CPUs, capped at 8).
- Agent analysis reads the `sc2build.v_*` views; AI is intentionally not embedded in the service.

## Tech tree assets

Icons are available from the TactiX StarCraft II mod:

`D:\Program Files\TactiX_1.2.3\Mods\StarCraft II Mod.zip`

The manifest has `Abbr`, Chinese `Desc`, and `Type` (0 action, 1 special, 2 unit, 3 building, 4 upgrade). Normalize TactiX abbreviations to sc2reader keys before use.

Extracted assets and data:

- `vue-app/public/sc2-icons/` - icons named by TactiX Abbr
- `scripts/extract_tactix_icons.py` - regenerate icons from the zip
- `scripts/build_catalog.py` - regenerate the catalog
- `scripts/fetch_level_icons.py` - fetch level-specific upgrade icons from Liquipedia
- `vue-app/src/data/sc2-catalog.json` - canonical key -> Abbr / official English / Chinese name
- `vue-app/src/data/tech-trees.json` - Protoss/Terran/Zerg node positions and prerequisites

English names follow Liquipedia Legacy of the Void; Chinese names follow the TactiX manifest.
