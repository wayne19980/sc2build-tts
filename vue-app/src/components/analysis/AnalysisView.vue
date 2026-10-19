<template>
  <div class="analysis-root">
    <aside class="sidebar">
      <section class="sidebar-section">
        <div class="section-heading">
          <span>赛事文件夹</span>
          <button class="icon-button" title="刷新" @click="loadFolders">↻</button>
        </div>
        <div class="folder-list">
          <button
            v-for="folder in folders"
            :key="folder.id"
            class="folder-row"
            :class="{ active: folder.id === activeFolderId }"
            @click="selectFolder(folder)"
          >
            <span class="folder-name">{{ folder.name }}</span>
            <span class="folder-count">{{ folder.game_count }}</span>
          </button>
          <div v-if="!folders.length" class="empty-hint">还没有导入文件夹</div>
        </div>
      </section>

      <section class="sidebar-section import-section">
        <div class="section-heading"><span>导入录像文件夹</span></div>
        <div class="path-row">
          <input
            v-model="importPath"
            class="path-input"
            placeholder="D:\Replays\Tournament"
            @keyup.enter="startImport"
          />
          <button v-if="isDesktop" class="ghost-button choose-button" @click="chooseFolder">
            选择
          </button>
        </div>
        <button class="primary-button" :disabled="!importPath.trim() || importing" @click="startImport">
          {{ importing ? '导入中…' : '开始导入' }}
        </button>
        <div v-if="importJob" class="import-status">
          <div class="import-line">
            <span>{{ importJob.phase }}</span>
            <span>{{ importJob.processed }}/{{ importJob.total }}</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: `${importJob.progress}%` }" />
          </div>
          <div class="import-meta">
            +{{ importJob.imported }} · ={{ importJob.skipped }} · !{{ importJob.errors.length }}
          </div>
        </div>
        <div v-if="error" class="error-text">{{ error }}</div>
      </section>

    </aside>

    <main class="main-panel">
      <template v-if="activeGame">
        <header class="game-header">
          <div class="game-title-block">
            <button class="back-button" @click="backToLibrary">← 对局列表</button>
            <div class="eyebrow">{{ activeGame.game.folder_name }}</div>
            <h1>{{ activeGame.game.map_name || 'Unknown Map' }}</h1>
            <div class="game-subline">
              <span>{{ activeGame.game.players }}</span>
              <span v-if="activeGame.game.winner">胜者 {{ activeGame.game.winner }}</span>
              <span>{{ formatClock(duration) }}</span>
            </div>
          </div>

          <div class="player-tabs">
            <button
              v-for="player in activeGame.players"
              :key="player.id"
              class="player-tab"
              :class="{ active: player.id === activePlayerId, winner: player.is_winner }"
              @click="selectPlayer(player.id)"
            >
              <span class="race-dot" :class="raceClass(player.race)" />
              <span>{{ player.name }}</span>
              <span v-if="player.is_winner" class="crown">★</span>
            </button>
            <button
              v-if="activeGame.players.length >= 2"
              class="split-toggle"
              :class="{ active: splitView }"
              @click="splitView = !splitView"
            >
              {{ splitView ? '单人' : '分屏' }}
            </button>
          </div>
        </header>

        <div class="tree-toolbar">
          <div class="legend">
            <span><i class="legend-dot locked" />未解锁</span>
            <span><i class="legend-dot building" />建造中</span>
            <span><i class="legend-dot done" />已完成</span>
          </div>
          <div class="toolbar-actions">
            <div class="segmented">
              <button
                :class="{ active: countMode === 'cumulative' }"
                @click="countMode = 'cumulative'"
              >
                累计
              </button>
              <button :class="{ active: countMode === 'alive' }" @click="countMode = 'alive'">
                存活
              </button>
            </div>
            <div v-if="isDesktop" class="overlay-controls">
              <button
                class="overlay-button"
                :class="{ active: overlayEnabled }"
                title="Overlay 开关 (Ctrl+Shift+O)"
                @click="toggleOverlay"
              >
                Overlay {{ overlayEnabled ? '关闭' : '开启' }}
              </button>
              <input
                v-model.number="overlayOpacity"
                class="overlay-opacity"
                type="range"
                min="0.25"
                max="0.9"
                step="0.01"
                title="Overlay 透明度"
              />
              <select v-model="overlayAnchor" class="anchor-select" title="Overlay 位置">
                <option value="top-center">顶部居中</option>
                <option value="top-left">左上</option>
                <option value="top-right">右上</option>
                <option value="bottom-left">左下</option>
                <option value="bottom-right">右下</option>
              </select>
            </div>
            <span v-if="overlayError" class="overlay-error-text">{{ overlayError }}</span>
            <span class="clock-readout">{{ formatClock(time) }}</span>
          </div>
        </div>

        <div class="tree-stage" :class="{ split: splitView }">
          <template v-if="splitView && activeGame.players.length >= 2">
            <PlayerTreePanel
              v-for="player in activeGame.players.slice(0, 2)"
              :key="player.id"
              :player="player"
              :time="time"
              :count-mode="countMode"
              :buildings="buildings"
              :units="units"
              :tech="tech"
            />
          </template>
          <ScaledTree
            v-else-if="race"
            :race="race"
            :player-id="activePlayerId || 0"
            :time="time"
            :count-mode="countMode"
            :buildings="playerBuildings"
            :units="playerUnits"
            :tech="playerTech"
          />
        </div>

        <UpgradeStrip v-if="race" :race="race" :time="time" :tech="playerTech" />

        <footer class="timeline-bar">
          <button class="play-button" @click="togglePlay">
            {{ playing ? '暂停' : '播放' }}
          </button>
          <button class="ghost-button" @click="resetTime">重置</button>
          <input
            v-model.number="time"
            class="timeline-slider"
            type="range"
            min="0"
            :max="duration"
            step="0.1"
            @input="pause"
          />
          <div class="speed-group">
            <button
              v-for="option in [1, 2, 4]"
              :key="option"
              :class="{ active: speed === option }"
              @click="speed = option"
            >
              {{ option }}x
            </button>
          </div>
          <span class="timeline-time">{{ formatClock(time) }} / {{ formatClock(duration) }}</span>
        </footer>
      </template>

      <ReplayLibrary
        v-else
        :replays="replays"
        :folder-name="activeFolderName"
        :loading="replaysLoading"
        @open="selectGame"
      />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { api } from '../../api'
import type {
  EventItem,
  FolderInfo,
  FolderReplay,
  GameDetail,
  GameSummary,
  ImportJob,
  OverlayAnchor,
  OverlayState,
  PlayerInfo,
  TechTiming,
  UnitLifecycle,
} from '../../types-analysis'
import { formatClock, raceFromName } from '../../data/catalog'
import {
  closeOverlayWindow,
  emitOverlayState,
  hideOverlayWindow,
  isTauriRuntime,
  listenOverlayEvent,
  openOverlayWindow,
  pickDirectory,
  positionOverlayWindow,
  registerOverlayShortcut,
} from '../../composables/useTauri'
import ReplayLibrary from './ReplayLibrary.vue'
import ScaledTree from './ScaledTree.vue'
import PlayerTreePanel from './PlayerTreePanel.vue'
import UpgradeStrip from './UpgradeStrip.vue'

const folders = ref<FolderInfo[]>([])
const replays = ref<FolderReplay[]>([])
const replaysLoading = ref(false)
const activeFolderId = ref<number | null>(null)
const activeGameId = ref<number | null>(null)
const activeGame = ref<GameDetail | null>(null)
const activePlayerId = ref<number | null>(null)
const splitView = ref(false)

const buildings = ref<EventItem[]>([])
const units = ref<UnitLifecycle[]>([])
const tech = ref<TechTiming[]>([])

const time = ref(0)
const playing = ref(false)
const speed = ref(1)
const countMode = ref<'cumulative' | 'alive'>('cumulative')
const error = ref('')

const importPath = ref('')
const importJob = ref<ImportJob | null>(null)
const importing = ref(false)
let importTimer: ReturnType<typeof setTimeout> | null = null

const isDesktop = isTauriRuntime()
const overlayEnabled = ref(false)
const overlayOpacity = ref(Number(localStorage.getItem('sc2-overlay-opacity-v2') || 0.55))
const overlayAnchor = ref<OverlayAnchor>(
  savedAnchor('sc2-overlay-anchor', 'top-center'),
)
const overlayError = ref('')
let overlayUnlisten: (() => void) | null = null
let overlayShortcutUnregister: (() => Promise<void>) | null = null
let overlaySyncTimer: number | null = null

let animationFrame: number | null = null
let lastFrame = 0

const duration = computed(() => {
  const gameDuration = activeGame.value?.game.duration_sec || 0
  if (gameDuration > 0) return gameDuration
  const maxEvent = Math.max(0, ...brandedTimes.value)
  return maxEvent
})

const brandedTimes = computed(() => [
  ...playerBuildings.value.map((event) => event.t_sec),
  ...playerUnits.value.map((unit) => unit.died_t_sec || unit.born_t_sec),
])

const activeFolderName = computed(
  () => folders.value.find((folder) => folder.id === activeFolderId.value)?.name || '',
)

const selectedPlayer = computed<PlayerInfo | null>(() => {
  if (!activeGame.value || activePlayerId.value === null) return null
  return activeGame.value.players.find((player) => player.id === activePlayerId.value) || null
})

const race = computed(() => raceFromName(selectedPlayer.value?.race))

const playerBuildings = computed(() =>
  buildings.value.filter((event) => event.player_id === activePlayerId.value),
)
const playerUnits = computed(() =>
  units.value.filter((unit) => unit.player_id === activePlayerId.value),
)
const playerTech = computed(() =>
  tech.value.filter((timing) => timing.player_id === activePlayerId.value),
)

onMounted(() => {
  loadFolders()
  window.addEventListener('resize', handleViewport)
  handleViewport()
  if (isDesktop) {
    void listenOverlayEvent('sc2-overlay-ready', () => {
      if (overlayEnabled.value) scheduleOverlaySync(true)
    }).then((unlisten) => {
      overlayUnlisten = unlisten
    })
    void registerOverlayShortcut(() => {
      void toggleOverlay()
    })
      .then((unregister) => {
        overlayShortcutUnregister = unregister
      })
      .catch((exc) => {
        overlayError.value = exc instanceof Error ? exc.message : String(exc)
      })
  }
})

onBeforeUnmount(() => {
  pause()
  window.removeEventListener('resize', handleViewport)
  if (importTimer) clearTimeout(importTimer)
  if (overlaySyncTimer) clearTimeout(overlaySyncTimer)
  overlayUnlisten?.()
  void overlayShortcutUnregister?.()
  void closeOverlayWindow()
})

watch([time, countMode, activeGameId, activePlayerId], () => {
  if (overlayEnabled.value) scheduleOverlaySync()
})

watch(overlayOpacity, (value) => {
  localStorage.setItem('sc2-overlay-opacity-v2', String(value))
  if (overlayEnabled.value) scheduleOverlaySync(true)
})

watch(overlayAnchor, (anchor) => {
  localStorage.setItem('sc2-overlay-anchor', anchor)
  if (overlayEnabled.value) void positionOverlayWindow(anchor)
})

async function loadFolders() {
  try {
    error.value = ''
    folders.value = await fetchFoldersWithRetry()
    if (activeFolderId.value === null && folders.value.length) {
      await selectFolder(folders.value[0])
    } else if (activeFolderId.value !== null) {
      await loadGames(activeFolderId.value)
    }
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : String(exc)
  }
}

async function fetchFoldersWithRetry(): Promise<FolderInfo[]> {
  let lastError: unknown = null
  for (let attempt = 0; attempt < 20; attempt += 1) {
    try {
      return await api.folders()
    } catch (exc) {
      lastError = exc
      await new Promise((resolve) => setTimeout(resolve, 500))
    }
  }
  throw lastError instanceof Error ? lastError : new Error(String(lastError))
}

async function selectFolder(folder: FolderInfo) {
  activeFolderId.value = folder.id
  activeGameId.value = null
  activeGame.value = null
  activePlayerId.value = null
  pause()
  await loadGames(folder.id)
}

async function loadGames(folderId: number) {
  replaysLoading.value = true
  try {
    replays.value = await api.folderReplays(folderId)
    if (activeGameId.value && !replays.value.some((game) => game.game_id === activeGameId.value)) {
      activeGameId.value = null
      activeGame.value = null
    }
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : String(exc)
  } finally {
    replaysLoading.value = false
  }
}

async function selectGame(game: GameSummary) {
  activeGameId.value = game.game_id
  pause()
  time.value = 0
  try {
    error.value = ''
    const [detail, buildingEvents, unitRows, techRows] = await Promise.all([
      api.game(game.game_id),
      api.buildings(game.game_id),
      api.units(game.game_id),
      api.tech(game.game_id),
    ])
    activeGame.value = detail
    buildings.value = buildingEvents
    units.value = unitRows
    tech.value = techRows
    activePlayerId.value = detail.players[0]?.id || null
    splitView.value = false
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : String(exc)
  }
}

function selectPlayer(playerId: number) {
  activePlayerId.value = playerId
}

function handleViewport() {
  if (window.innerWidth < 1100) splitView.value = false
}

function backToLibrary() {
  pause()
  activeGame.value = null
  activePlayerId.value = null
  activeGameId.value = null
  splitView.value = false
}

function togglePlay() {
  if (playing.value) pause()
  else play()
}

function play() {
  if (!activeGame.value) return
  playing.value = true
  lastFrame = performance.now()
  animationFrame = requestAnimationFrame(tick)
}

function tick(now: number) {
  if (!playing.value) return
  const delta = (now - lastFrame) / 1000
  lastFrame = now
  time.value = Math.min(duration.value, time.value + delta * speed.value)
  if (time.value >= duration.value) {
    pause()
    return
  }
  animationFrame = requestAnimationFrame(tick)
}

function pause() {
  playing.value = false
  if (animationFrame !== null) {
    cancelAnimationFrame(animationFrame)
    animationFrame = null
  }
}

function resetTime() {
  pause()
  time.value = 0
}

function raceClass(raceName: string | null): string {
  return raceFromName(raceName)?.toLowerCase() || ''
}

async function chooseFolder() {
  try {
    const selected = await pickDirectory()
    if (selected) importPath.value = selected
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : String(exc)
  }
}

function buildOverlayState(): OverlayState {
  return {
    gameId: activeGameId.value,
    playerId: activePlayerId.value,
    playerName: selectedPlayer.value?.name || '',
    mapName: activeGame.value?.game.map_name || '',
    race: race.value,
    time: time.value,
    duration: duration.value,
    countMode: countMode.value,
    opacity: overlayOpacity.value,
  }
}

function savedAnchor(key: string, fallback: OverlayAnchor): OverlayAnchor {
  const value = localStorage.getItem(key) as OverlayAnchor | null
  const allowed: OverlayAnchor[] = [
    'top-left',
    'top-center',
    'top-right',
    'bottom-left',
    'bottom-right',
  ]
  return value && allowed.includes(value) ? value : fallback
}

function scheduleOverlaySync(immediate = false) {
  if (!isDesktop || !overlayEnabled.value) return
  if (immediate) {
    if (overlaySyncTimer) {
      clearTimeout(overlaySyncTimer)
      overlaySyncTimer = null
    }
    void emitOverlayState(buildOverlayState())
    return
  }
  if (overlaySyncTimer) return
  overlaySyncTimer = window.setTimeout(() => {
    overlaySyncTimer = null
    void emitOverlayState(buildOverlayState())
  }, 100)
}

async function toggleOverlay() {
  if (!isDesktop) {
    overlayError.value = 'Overlay 需要在 Tauri 桌面端运行'
    return
  }
  overlayError.value = ''
  try {
    if (overlayEnabled.value) {
      await hideOverlayWindow()
      overlayEnabled.value = false
      return
    }
    await openOverlayWindow(overlayAnchor.value)
    overlayEnabled.value = true
    scheduleOverlaySync(true)
  } catch (exc) {
    overlayError.value = exc instanceof Error ? exc.message : String(exc)
  }
}

async function startImport() {
  const path = importPath.value.trim()
  if (!path || importing.value) return
  importing.value = true
  error.value = ''
  try {
    importJob.value = await api.createImport(path)
    pollImport(importJob.value.id)
  } catch (exc) {
    importing.value = false
    error.value = exc instanceof Error ? exc.message : String(exc)
  }
}

function pollImport(jobId: string) {
  if (importTimer) clearTimeout(importTimer)
  importTimer = setTimeout(async () => {
    try {
      const job = await api.importJob(jobId)
      importJob.value = job
      if (job.status === 'done' || job.status === 'failed') {
        importing.value = false
        await loadFolders()
        if (activeFolderId.value !== null) await loadGames(activeFolderId.value)
      } else {
        pollImport(jobId)
      }
    } catch (exc) {
      importing.value = false
      error.value = exc instanceof Error ? exc.message : String(exc)
    }
  }, 700)
}
</script>

<style scoped>
.analysis-root {
  display: flex;
  height: 100%;
  min-height: 0;
  background: #050811;
  color: #dce8f8;
  font-family: 'Noto Sans SC', 'Segoe UI', sans-serif;
}

.sidebar {
  width: 310px;
  flex: none;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-right: 1px solid #142238;
  background:
    linear-gradient(180deg, rgba(17, 31, 53, 0.9), rgba(5, 9, 17, 0.98)),
    #070b14;
}

.sidebar-section {
  padding: 14px 14px 10px;
  border-bottom: 1px solid #101d2f;
  min-height: 0;
}

.games-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  color: #8ca6c8;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.muted {
  color: #4e6888;
}

.icon-button,
.ghost-button {
  border: 1px solid #1d3352;
  background: transparent;
  color: #8ca6c8;
  border-radius: 6px;
  cursor: pointer;
}

.icon-button {
  width: 24px;
  height: 24px;
}

.folder-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 150px;
  overflow: auto;
}

.folder-row,
.game-row {
  width: 100%;
  border: 1px solid transparent;
  background: transparent;
  color: #c6d6ea;
  text-align: left;
  cursor: pointer;
  border-radius: 8px;
}

.folder-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 9px;
  font-size: 13px;
}

.folder-row:hover,
.game-row:hover {
  background: #0d1929;
}

.folder-row.active,
.game-row.active {
  border-color: #2f6caf;
  background: linear-gradient(90deg, rgba(47, 108, 175, 0.22), rgba(47, 108, 175, 0.06));
}

.folder-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.folder-count {
  color: #5f7d9f;
  font-size: 11px;
}

.import-section {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.path-input {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 9px;
  border-radius: 7px;
  border: 1px solid #1d3352;
  background: #070d18;
  color: #cfe0f4;
  font-size: 11px;
  outline: none;
}

.path-input:focus {
  border-color: #2f6caf;
}

.primary-button {
  padding: 8px 10px;
  border: 1px solid #2f6caf;
  border-radius: 7px;
  background: linear-gradient(180deg, #1f5da5, #174477);
  color: #eaf4ff;
  font-size: 12px;
  cursor: pointer;
}

.primary-button:disabled {
  opacity: 0.45;
  cursor: default;
}

.import-status {
  padding: 7px 8px;
  border: 1px solid #162a45;
  border-radius: 7px;
  background: #070d18;
  font-size: 10px;
  color: #8ca6c8;
}

.import-line,
.import-meta {
  display: flex;
  justify-content: space-between;
}

.import-meta {
  margin-top: 4px;
  color: #5f7d9f;
}

.progress-track {
  height: 4px;
  margin-top: 6px;
  border-radius: 2px;
  background: #122138;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2f7fe0, #63b3ff);
  transition: width 0.25s ease;
}

.error-text {
  color: #ff7d7d;
  font-size: 11px;
  word-break: break-word;
}

.game-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
  overflow: auto;
  min-height: 0;
}

.game-row {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 7px 9px;
  font-size: 12px;
}

.game-map {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.game-players {
  color: #7f99bb;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.game-meta {
  display: flex;
  justify-content: space-between;
  color: #4f6b8c;
  font-size: 10px;
}

.winner {
  color: #d9b45b;
}

.empty-hint {
  padding: 6px 2px;
  color: #4f6b8c;
  font-size: 11px;
}

.main-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.game-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 22px 10px;
  border-bottom: 1px solid #101d2f;
  background: rgba(7, 12, 22, 0.9);
}

.back-button {
  margin-bottom: 4px;
  padding: 2px 0;
  border: 0;
  background: transparent;
  color: #5f7d9f;
  font-size: 10px;
  cursor: pointer;
}

.back-button:hover {
  color: #9fc3ef;
}

.eyebrow {
  color: #5f7d9f;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.game-title-block h1 {
  margin: 3px 0 4px;
  font-size: 22px;
  line-height: 1.2;
  background: linear-gradient(90deg, #dcecff, #7fb9ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.game-subline {
  display: flex;
  gap: 14px;
  color: #7893b5;
  font-size: 12px;
}

.player-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.player-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  border: 1px solid #1d3352;
  border-radius: 8px;
  background: #080f1c;
  color: #a9bfd8;
  font-size: 12px;
  cursor: pointer;
}

.player-tab.active {
  border-color: #3d7fc4;
  background: #0e1d30;
  color: #e8f3ff;
  box-shadow: 0 0 12px rgba(61, 127, 196, 0.25);
}

.player-tab.winner .crown {
  color: #e5bd5f;
}

.split-toggle {
  padding: 7px 10px;
  border: 1px solid #1d3352;
  border-radius: 8px;
  background: #080f1c;
  color: #8ca6c8;
  font-size: 11px;
  cursor: pointer;
}

.split-toggle.active {
  border-color: #3d7fc4;
  background: #173a61;
  color: #e8f4ff;
}

.race-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6f89ad;
}

.race-dot.p {
  background: #b197fc;
  box-shadow: 0 0 7px rgba(177, 151, 252, 0.7);
}

.race-dot.t {
  background: #74c0fc;
  box-shadow: 0 0 7px rgba(116, 192, 252, 0.7);
}

.race-dot.z {
  background: #69db7c;
  box-shadow: 0 0 7px rgba(105, 219, 124, 0.7);
}

.tree-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 22px;
  border-bottom: 1px solid #0e1a2b;
  background: rgba(6, 11, 20, 0.65);
}

.legend {
  display: flex;
  gap: 14px;
  color: #6f89ad;
  font-size: 11px;
}

.legend span {
  display: flex;
  align-items: center;
  gap: 5px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  background: #31527a;
}

.legend-dot.locked {
  opacity: 0.25;
}

.legend-dot.building {
  opacity: 0.6;
  animation: legend-pulse 1.4s ease-in-out infinite;
}

.legend-dot.done {
  background: #5aa7ed;
  box-shadow: 0 0 8px rgba(90, 167, 237, 0.7);
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.segmented {
  display: flex;
  border: 1px solid #1d3352;
  border-radius: 7px;
  overflow: hidden;
}

.segmented button,
.speed-group button {
  padding: 4px 9px;
  border: none;
  background: transparent;
  color: #6f89ad;
  font-size: 11px;
  cursor: pointer;
}

.segmented button.active,
.speed-group button.active {
  background: #173a61;
  color: #d9ecff;
}

.clock-readout {
  color: #9fc3ef;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 13px;
}

.tree-stage {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
}

.tree-stage.split {
  gap: 1px;
  background: #0a1422;
}

.timeline-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 22px;
  border-top: 1px solid #16263d;
  background: rgba(6, 11, 20, 0.96);
}

.play-button {
  min-width: 64px;
  padding: 7px 12px;
  border: 1px solid #2f6caf;
  border-radius: 7px;
  background: linear-gradient(180deg, #1f5da5, #174477);
  color: #eaf4ff;
  font-size: 12px;
  cursor: pointer;
}

.ghost-button {
  padding: 6px 10px;
  font-size: 11px;
}

.timeline-slider {
  flex: 1;
  accent-color: #4b9bf0;
  cursor: pointer;
}

.speed-group {
  display: flex;
  border: 1px solid #1d3352;
  border-radius: 7px;
  overflow: hidden;
}

.timeline-time {
  min-width: 104px;
  color: #8ca6c8;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 11px;
  text-align: right;
}

.path-row {
  display: flex;
  gap: 6px;
}

.path-row .path-input {
  flex: 1;
  min-width: 0;
}

.choose-button {
  flex: none;
  padding: 0 9px;
  font-size: 11px;
}

.overlay-controls {
  display: flex;
  align-items: center;
  gap: 7px;
}

.overlay-button {
  padding: 4px 9px;
  border: 1px solid #1d3352;
  border-radius: 7px;
  background: transparent;
  color: #7893b5;
  font-size: 11px;
  cursor: pointer;
}

.overlay-button.active {
  border-color: #3d7fc4;
  background: #173a61;
  color: #d9ecff;
  box-shadow: 0 0 10px rgba(61, 127, 196, 0.25);
}

.overlay-opacity {
  width: 70px;
  accent-color: #4b9bf0;
}

.anchor-select {
  padding: 3px 5px;
  border: 1px solid #1d3352;
  border-radius: 6px;
  background: #080f1c;
  color: #9fb8d8;
  font-size: 10px;
  outline: none;
}

.overlay-error-text {
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #ff8c8c;
  font-size: 10px;
}

.empty-main {
  flex: 1;
  display: grid;
  place-content: center;
  text-align: center;
  color: #6f89ad;
  position: relative;
  overflow: hidden;
}

.empty-main h2 {
  margin: 0 0 6px;
  color: #b7cde6;
  font-size: 22px;
}

.empty-main p {
  margin: 0;
  font-size: 13px;
}

.empty-glow {
  position: absolute;
  width: 420px;
  height: 420px;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: radial-gradient(circle, rgba(47, 108, 175, 0.16), transparent 65%);
  pointer-events: none;
}

@keyframes legend-pulse {
  0%,
  100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.75;
  }
}
</style>
