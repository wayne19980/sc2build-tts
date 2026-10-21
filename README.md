# sc2build-tts

Local StarCraft II replay analysis desktop app. Import a folder of `.SC2Replay`
files, extract building/tech/unit events, and explore the build order on an
interactive tech tree. The UI is available in Chinese and English, and the
desktop build can read the build order aloud and show a compact in-game overlay.

![Replay library](docs/screenshots/library.png)

![Split tech tree](docs/screenshots/split.png)

## Features

- Import a folder of replays (or a single replay file) and deduplicate by hash.
- Per-player tech tree with cumulative / alive unit counts.
- Worker count next to each player's main base.
- Split view by default when a game has two players.
- Unified construction strip: buildings, unit training, Zerg morphs, active
  upgrades and Carrier interceptors. Voice announcements skip auto-spawned
  units such as interceptors.
- Attack/armor lines collapse to one icon (current level), with a progress bar
  while the next level is being researched.
- Chinese / English switch that also drives voice language and display names.
- Voice reader and a click-through overlay for windowed / borderless SC2.
- Everything runs locally: no cloud service or account.

## Tech stack

- Frontend: Vue 3, Vite, TypeScript, Tailwind CSS
- Desktop shell: Tauri 2 (Rust)
- Backend: Python 3.12, FastAPI, SQLAlchemy, psycopg 3
- Database: PostgreSQL (embedded `pgserver` in release builds, external in dev
  when configured)
- Replay parsing: `sc2reader` + `spawningtool`

## Requirements

- Windows 10/11 x64
- [WebView2 runtime](https://developer.microsoft.com/microsoft-edge/webview2/)
  (preinstalled on current Windows 11)
- Node.js 22+ and pnpm 10
- Rust stable with the MSVC toolchain and Visual Studio Build Tools
  ("Desktop development with C++")
- Python 3.12. [uv](https://docs.astral.sh/uv/) is recommended.
- PostgreSQL 14+ only if you want to use an external database instead of the
  embedded one.

## Getting started (development)

### 1. Clone

```bash
git clone https://github.com/wayne19980/sc2build-tts.git
cd sc2build-tts
```

### 2. Create the Python environment

With uv (recommended):

```bash
uv venv --python 3.12 --seed .venv
uv pip install --python .venv/Scripts/python.exe -r services/analyzer/requirements.txt
```

Without uv:

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r services\analyzer\requirements.txt
```

If `uv` is not found, open a new terminal after installing it so the updated
`PATH` is picked up.

### 3. Install frontend dependencies

```bash
cd vue-app
pnpm install
```

### 4. Run the desktop app

```bash
pnpm tauri:dev
```

This starts the Vite dev server and the Tauri window. In debug mode the app also
spawns the Python backend from `.venv` on `http://127.0.0.1:8765`.

The first run compiles the Rust dependencies and can take several minutes.

### Database behavior

By default **development uses an embedded PostgreSQL** started by the backend
(`pgserver`), so no database setup is required:

- Data directory: `%LOCALAPPDATA%\sc2build-tts\pgdata`
- The server is started and stopped together with the app.
- Schema and migrations are applied automatically on startup.
- While the app is running it listens on `127.0.0.1` on a random port. The port
  is the 4th line of `%LOCALAPPDATA%\sc2build-tts\pgdata\postmaster.pid`.
  Connection details for tools such as Navicat: user `postgres`, empty
  password, database `postgres`. The server stops when the app exits.

To use an external PostgreSQL instead, create a `.env` file in the repository
root:

```bash
copy .env.example .env
```

Then set `DATABASE_URL`, for example:

```dotenv
DATABASE_URL=postgresql://postgres:your-password@localhost:5432/postgres
SC2_SCHEMA=sc2build
```

When `.env` exists the backend uses that database and does not start an
embedded server. Release builds force the bundled embedded database
(`SC2_EMBEDDED_PG=1`), so no `.env` is required.

### Import replays

Use **导入录像 / Import replays** in the sidebar to import a folder or a single
`.SC2Replay` file. Files are hashed first, so re-importing the same folder skips
existing games.

A sample replay is available in `test/`.

From the command line (requires an external database from `.env`, because the
CLI process does not start the app's embedded server):

```bash
.venv\Scripts\python.exe services\analyzer\scripts\import_folder.py --folder test
```

To reset the embedded development database, close the app and delete
`%LOCALAPPDATA%\sc2build-tts\pgdata`.

## Build a Windows installer

Build the Python sidecar first, then the Tauri bundle:

```bash
.venv\Scripts\python.exe scripts\build_sidecar.py
cd vue-app
pnpm tauri:build
```

Artifacts:

- `vue-app/src-tauri/target/release/bundle/msi/*.msi`
- `vue-app/src-tauri/target/release/bundle/nsis/*.exe`

The sidecar binary is generated at
`vue-app/src-tauri/binaries/sc2analyzer-api-<target-triple>.exe` and is not
committed. If Tauri reports that the resource path does not exist, run
`scripts/build_sidecar.py` first.

Updater artifacts are signed only when `TAURI_SIGNING_PRIVATE_KEY` is set (see
`.github/workflows/release.yml`).

## Tests

```bash
cd services/analyzer
..\..\.venv\Scripts\python.exe -m pytest -q
```

## Project layout

```
services/analyzer/       Python API, replay parsing, migrations
  sc2analyzer/           FastAPI app, importer, database, embedded pgserver
  sql/migrations/        Ordered SQL migrations
  scripts/               init_db.py, import_folder.py
vue-app/                 Vue 3 frontend + Tauri shell
  src/                   UI components and tech tree data
  public/sc2-icons/      Unit/building/upgrade icons
  src-tauri/             Rust desktop shell and Tauri configuration
scripts/                 Asset generation and sidecar/release helpers
test/                    Sample replay used by tests and demos
```

## Data notes

- `t_sec` is the in-game display time (`frame / frames_per_second`, 22.4 on
  Faster).
- `events.kind` includes `order`, `build_start`, `build_done`,
  `unit_training_start`, `unit_born`, `unit_died`, `unit_morph`,
  `upgrade_done` and `ability`.
- All application objects live in the `sc2build` schema (override with
  `SC2_SCHEMA`); migrations are tracked in `sc2build.schema_migrations`.

## Troubleshooting

- **`ring` fails with `cl.exe` error D8050 while building in debug**: this is
  usually stale build state or an outdated MSVC toolchain. Run `cargo clean` in
  `vue-app/src-tauri` and rebuild; if it persists, update Visual Studio Build
  Tools.
- **Tauri build says `binaries/sc2analyzer-api-...exe` is missing**: run
  `.venv\Scripts\python.exe scripts\build_sidecar.py`.
- **`DATABASE_URL is not set`**: development started without `.env` and the
  embedded database could not start. Check that no other process is using the
  data directory, or delete `%LOCALAPPDATA%\sc2build-tts\pgdata` and retry.
- **Overlay does not appear over the game**: only windowed or
  borderless-fullscreen SC2 is supported; exclusive fullscreen cannot show
  overlays.
- **No WebView2**: install the Evergreen WebView2 runtime.

## License

GPL-3.0. See [LICENSE](LICENSE).
