# Feature List

## Backend

- [x] PostgreSQL schema `sc2build`
- [x] Replay metadata, players, build events, upgrades, stats
- [x] Unit lifecycle (production / alive at time)
- [x] Folder import with hash dedupe
- [x] Agent-facing SQL views
- [x] Parser tests
- [x] SQL migrations with checksums
- [x] Run pending migrations on API startup
- [x] FastAPI service
- [x] Background import job + progress endpoint
- [x] Folder/game/timeline/units API endpoints

## Desktop

- [x] Tauri native folder picker
- [x] Python API packaged as a Tauri sidecar
- [x] Backend auto-start in Tauri dev / release
- [x] Backend cleanup on main-window close
- [x] Global shortcut for overlay toggle (`Ctrl+Shift+O`)

## Frontend

- [x] Folder library grouped by import folder
- [x] Replay library with units and early/mid/late upgrades
- [x] Split-screen 1v1 tech trees (compact spacing, no aspect lock)
- [x] Auto-fit tech tree from 800x600 to 4K
- [x] Icon-only Protoss/Terran/Zerg tech trees
- [x] Building states: locked / under construction / completed
- [x] Morph-aware building counts (base + morph badge)
- [x] Unlock flash animation
- [x] Rounded orthogonal tech-tree connectors
- [x] Unit count badge (cumulative or alive)
- [x] Timeline scrubber and playback (1x/2x/4x/8x)
- [x] Voice build-order reader with TTS and PiP
- [x] Single replay file picker + drag/drop
- [x] Folder deletion
- [x] Three tech-tree JSON layouts derived from the reference images
- [x] TactiX icon mapping and asset extraction
- [x] Level-specific attack/armor/shield icons

## Overlay

- [x] Tauri transparent always-on-top window
- [x] Mouse click-through
- [x] Fixed position, configurable opacity
- [x] Sync selected player/time with main window
- [x] Compact 760x220 overlay window (not full-screen)
- [x] Time + upcoming build actions strip
- [x] Mini tech tree for all future unlocks, 60s timestamps highlighted
- [x] Window position presets with SC2-safe top offsets
- [ ] Borderless fullscreen validation

## Agent

- [x] Stable database views for direct agent access
- [ ] `AGENT.md` query examples / schema notes
- [ ] Optional `agent_analyses` write-back usage
