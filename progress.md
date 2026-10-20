## 2026-10-20 (v0.6.0 / v0.6.1 / v0.6.4)

- Release builds now use embedded PostgreSQL via `pgserver`; no external PG or .env needed.
- Debug builds still use the external PostgreSQL from repo `.env`.
- Embedded PG data lives in the Tauri app data directory; sidecar starts/stops it.
- Parent-process watchdog stops pgserver when the app exits or is force-killed.
- Added Tauri updater with signed update artifacts and `latest.json`.
- Update endpoints use gh-proxy with GitHub fallback.
- Added startup update check, manual check button, progress and restart flow.
- Signing public key added to config; private key is kept outside the repo.
- Updater config is a separate `tauri.updater.conf.toml`; normal builds work without signing.
- v0.6.1 fixes the release workflow config path and keeps unsigned builds available.
- v0.6.4 uses a TOML override so CI parses the updater config correctly and ignores the unused password secret.

## 2026-10-20 (v0.5.2)

- Attack/armor/shield levels 1/2/3 now show in the upgrade strip with level-specific icons.
- Construction strip is icon-only: bottom progress bar, plain white count (shown when >1).
- Tech-tree buildings and upgrade icons show progress bars while constructing.
- All count badges are now plain white bottom-right numbers.
- Global Chinese/English switch drives UI, voice language, overlay and unit/build names.
- Overlay toggle now also opens and starts the voice reader; disabling overlay stops it.
- Voice reader merges repeated orders within a 4-second window (e.g. "Marine x5").
- Fixed duplicate global-shortcut registration on HMR reload.
- Version 0.5.2 prepared for release.

# Progress

## 2026-10-19

Done:
- PostgreSQL schema `sc2build` (no `public` objects).
- Backend scaffold in `services/analyzer`.
- Replay parser: buildings, units, morphs, upgrades, stats, abilities.
- Unit lifecycle table for cumulative production and alive-at-time queries.
- Folder import with SHA-256 dedupe.
- Agent-facing `v_*` views.
- Parser tests pass against `test/clem(w) vs classic g1 old republic.SC2Replay`.
- Ordered SQL migrations with checksums; API runs pending migrations on startup.

- FastAPI service with background import jobs and read endpoints.
- Verified migration bootstrap, test replay import, health/folders/games/tech/alive/production endpoints.
- TactiX icons extracted to `vue-app/public/sc2-icons` (172 PNGs).
- Official catalog names from Liquipedia, Chinese names from TactiX.
- Three icon-only tech-tree layouts (Protoss/Terran/Zerg).
- New Vue analysis view: folder/game browser, player switch, timeline scrub, building states, unit count badges, upgrade strip.
- Verified in browser via Playwright at 1920x1080.
- Normalized legacy Chinese unit/building names to Liquipedia/TactiX official names.
- Tauri main window switched to a normal desktop window.
- Native directory picker via `tauri-plugin-dialog`.
- Overlay window implementation: transparent, always-on-top, skip taskbar, non-focusable, click-through, fixed position, opacity control.
- Main window sends selected game/player/time/count-mode/opacity to the overlay via Tauri events.
- Overlay view renders the same tech tree scaled to fit.
- `cargo check`, `vue-tsc`, Vite build and pytest all pass.
- Python API packaged with PyInstaller into a Tauri sidecar (30 MB).
- Tauri Rust spawns the backend automatically: `.venv` Python in debug,
  bundled sidecar in release; verified health endpoint after launch.
- Frontend retries the API while the backend starts.
- Tauri kills the backend when the main window closes; a Python parent-PID
  watchdog also stops the backend if the app is force-killed.
- Global shortcut `Ctrl+Shift+O` toggles the overlay.
- Verified through Tauri WebView2 CDP: overlay window creation, state sync,
  time updates, unit badge updates and opacity sync.
- Vite now ignores `src-tauri` so target build files do not crash the watcher.
- Overlay redesigned after `suck-utilities` reference:
  - compact 760x220 window instead of a full-screen transparent window
  - build strip: current time + 4 upcoming/past build actions
  - mini tech tree: unlocks in the next ~30 seconds
  - one window position selector (top-left/center/right, bottom-left/right)
  - verified through Tauri CDP (size, content, time sync, position)
- Analysis tech tree now auto-fits width/height from 800x600 to 4K.
- Dense tree layout with larger building/unit icons.
- Split-screen mode for 1v1: both players' trees side by side.
- New replay library: folder list on the left, replay rows on the right.
  - both players' races and results
  - top units with counts
  - upgrades grouped into early/mid/late phases (0-6:00, 6:00-14:00, 14:00+)
- Tauri minimum window size lowered to 800x600.
- Parser now resolves a building/unit type at the event frame via `type_history`,
  so Gateway completions stay Gateway while WarpGate morphs are separate.
- Base building counts include morphs; Gateway shows a small WarpGate morph
  badge with its own count. Other morph targets that are tree nodes use their
  own node counts.
- Replay library no longer truncates unit lists to Top 5.
- Overlay top-center anchors at y=0; top-left/right at y=96 to clear SC2 resource bars.
- Overlay default opacity lowered to 0.55 and window tightened to 760x220.
- Mini tech tree now lists all future unlocks (up to 16, with +N overflow);
  timestamps within 60 seconds are highlighted.
- Tech-tree connectors replaced with rounded orthogonal paths and a subtle glow;
  no arrowheads, icons sit on top.
- New unlocks/buildings flash brightly for ~1.2s when the timeline crosses them.
- Split mode uses compact column spacing so both trees use more width.
- Library unit icons enlarged to 38px with count badges in the top-right corner;
  all units are shown (no Top 5 / +N truncation).

- Version bumped to 0.4.0.
- Old VPS deploy workflow replaced with tag-triggered Windows release workflow.

Next:
- Validate overlay against a running SC2 borderless-fullscreen window.
- Refine tech-tree layout and responsive fit.
- Agent query examples for the `v_*` views.
