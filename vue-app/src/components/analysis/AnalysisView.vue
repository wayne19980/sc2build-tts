<template>
  <div class="analysis-root">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-inner">
        <div class="sidebar-bar" title="点击收起侧栏" @click="sidebarCollapsed = true">
          <span class="sidebar-bar-title">录像库</span>
          <button
            class="icon-button collapse-button"
            title="收起侧栏"
            @click.stop="sidebarCollapsed = true"
          >
            «
          </button>
        </div>
        <section class="sidebar-section">
          <div class="section-heading">
            <span>赛事文件夹</span>
            <button class="icon-button" title="刷新" @click="loadFolders">↻</button>
          </div>
          <div class="folder-list">
            <div
              v-for="folder in folders"
              :key="folder.id"
              class="folder-row"
              :class="{ active: folder.id === activeFolderId }"
              @click="selectFolder(folder)"
            >
              <span class="folder-name">{{ folder.name }}</span>
              <span class="folder-count">{{ folder.game_count }}</span>
              <button
                class="folder-delete"
                title="删除文件夹"
                @click.stop="removeFolder(folder)"
              >
                ×
              </button>
            </div>
            <div v-if="!folders.length" class="empty-hint">还没有导入文件夹</div>
          </div>
        </section>

        <section class="sidebar-section import-section">
          <div class="section-heading"><span>导入录像</span></div>
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
          <div class="import-buttons">
            <button class="primary-button" :disabled="!importPath.trim() || importing" @click="startImport">
              {{ importing ? '导入中…' : '导入文件夹' }}
            </button>
            <button
              v-if="isDesktop"
              class="ghost-button file-button"
              :disabled="importing"
              @click="chooseReplay"
            >
              选择录像文件
            </button>
          </div>
          <div class="import-hint">也可以把单个 .SC2Replay 直接拖进窗口</div>
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
      </div>
    </aside>

    <button
      v-if="sidebarCollapsed"
      class="sidebar-expand"
      title="展开侧栏"
      @click="sidebarCollapsed = false"
    >
      »
    </button>

    <main class="main-panel">
      <div v-if="backendStarting" class="backend-status">
        <span class="status-dot" />
        {{ english ? 'Starting local database (first launch may take a minute)…' : '正在启动本地数据库（首次启动可能需要一分钟）…' }}
      </div>
      <template v-if="activeGame">
        <header class="game-header">
          <button class="back-button" @click="backToLibrary">← 对局列表</button>
          <div class="header-folder" :title="activeGame.game.folder_name">
            {{ activeGame.game.folder_name }}
          </div>
          <h1 class="header-map" :title="activeGame.game.map_name || 'Unknown Map'">
            {{ activeGame.game.map_name || 'Unknown Map' }}
          </h1>

          <div class="player-tabs">
            <template v-for="(player, index) in activeGame.players" :key="player.id">
              <span v-if="index > 0" class="versus">vs</span>
              <button
                class="player-tab"
                :class="{ active: player.id === activePlayerId, winner: player.is_winner }"
                @click="selectPlayer(player.id)"
              >
                <span class="race-icon" :class="raceClass(player.race)">
                  {{ raceLetter(player.race) }}
                </span>
                <span class="player-tab-name">{{ player.name }}</span>
                <span v-if="player.is_winner" class="crown">★</span>
              </button>
            </template>
          </div>

          <button
            v-if="activeGame.players.length >= 2"
            class="split-switch"
            :class="{ active: splitView }"
            :title="splitView ? '关闭分屏' : '开启分屏'"
            @click="splitView = !splitView"
          >
            <span class="split-switch-track"><span class="split-switch-knob" /></span>
            <span class="split-switch-label">分屏</span>
          </button>

          <div class="header-metrics">
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
          </div>
        </header>

        <div v-if="!splitView || isDesktop" class="tree-toolbar">
          <div class="toolbar-actions">
            <div class="segmented" v-if="!splitView">
              <button
                :class="{ active: singleViewMode === 'canvas' }"
                @click="singleViewMode = 'canvas'"
              >
                全景
              </button>
              <button
                :class="{ active: singleViewMode === 'flow' }"
                @click="singleViewMode = 'flow'"
              >
                自适应
              </button>
            </div>
            <div v-if="isDesktop" class="overlay-controls">
              <button
                class="overlay-button"
                :class="{ active: overlayEnabled }"
                title="Overlay 与语音播报开关 (Ctrl+Shift+O)"
                @click="toggleOverlay"
              >
                Overlay/语音 {{ overlayEnabled ? '关闭' : '开启' }}
              </button>
              <div ref="overlaySettingsRef" class="overlay-settings-picker">
                <button
                  class="overlay-settings-button"
                  :class="{ active: overlaySettingsOpen }"
                  title="Overlay 设置"
                  @click="overlaySettingsOpen = !overlaySettingsOpen"
                >
                  设置
                </button>
                <div v-if="overlaySettingsOpen" class="overlay-settings-panel" @click.stop>
                  <label class="overlay-setting-row">
                    <span>语音速度</span>
                    <b>{{ voiceRate.toFixed(1) }}x</b>
                    <input v-model.number="voiceRate" type="range" min="0.8" max="2.5" step="0.1" />
                  </label>
                  <label class="overlay-setting-row">
                    <span>播报农民</span>
                    <input v-model="voiceIncludeWorkers" class="overlay-setting-check" type="checkbox" />
                  </label>
                  <label class="overlay-setting-row">
                    <span>透明度</span>
                    <b>{{ Math.round(overlayOpacity * 100) }}%</b>
                    <input v-model.number="overlayOpacity" type="range" min="0.1" max="1" step="0.01" />
                  </label>
                  <label class="overlay-setting-row">
                    <span>位置</span>
                    <select v-model="overlayAnchor">
                      <option value="top-center">顶部居中</option>
                      <option value="top-left">左上</option>
                      <option value="top-right">右上</option>
                      <option value="bottom-left">左下</option>
                      <option value="bottom-right">右下</option>
                    </select>
                  </label>
                  <label class="overlay-setting-row">
                    <span>显示器</span>
                    <select v-model.number="overlayMonitor">
                      <option :value="-1">跟随主窗口</option>
                      <option v-for="(monitor, index) in monitors" :key="index" :value="index">
                        {{ monitor.name }} · {{ monitor.width }}×{{ monitor.height }}
                      </option>
                    </select>
                  </label>
                </div>
              </div>
            </div>
            <span v-if="overlayError" class="overlay-error-text">{{ overlayError }}</span>
          </div>
        </div>

        <div class="tree-stage" :class="{ split: splitView }">
          <template v-if="splitView && (activeGame?.players.length ?? 0) >= 2">
            <PlayerTreePanel
              v-for="player in activeGame?.players.slice(0, 2)"
              :key="player.id"
              :production="productionTasksFor(player.id)"
              :player="player"
              :time="time"
              :count-mode="countMode"
              :buildings="buildings"
              :units="units"
              :tech="tech"
              :orders="orders"
              :speed="speed"
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
            :orders="orders"
            :production="productionTasksFor(activePlayerId || 0)"
            :view-mode="singleViewMode"
          />
        </div>

        <ConstructionStrip :strips="constructionStrips" />

        <UpgradeStrip v-if="race" :rows="upgradeRows" :time="time" />

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
              v-for="option in [1, 2, 4, 8, 16, 24]"
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
  ConstructionGroupView,
  ConstructionStripView,
  EventItem,
  FolderInfo,
  FolderReplay,
  GameDetail,
  GameSummary,
  ImportJob,
  OverlayAnchor,
  OverlayState,
  PlayerInfo,
  ProductionTaskView,
  TechTiming,
  UnitLifecycle,
  UpgradeStripRow,
} from '../../types-analysis'
import { AUTO_SPAWNED_UNITS, formatClock, itemIconUrl, raceFromName, resolveItem } from '../../data/catalog'
import {
  closeOverlayWindow,
  emitOverlayState,
  hideOverlayWindow,
  isTauriRuntime,
  listMonitors,
  listenOverlayEvent,
  openOverlayWindow,
  pickDirectory,
  pickReplayFile,
  positionOverlayWindow,
  registerOverlayShortcut,
  listenDragDrop,
  type OverlayMonitor,
} from '../../composables/useTauri'
import { useVoiceReader } from '../../composables/useVoiceReader'
import { SC2_FASTER_REAL_FACTOR } from '../../utils'
import { useLanguage } from '../../composables/useLanguage'
import ConstructionStrip from './ConstructionStrip.vue'
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
const splitView = ref(true)
const singleViewMode = ref<'canvas' | 'flow'>('canvas')
const sidebarCollapsed = ref(localStorage.getItem('sc2-sidebar-collapsed') === '1')
const { english, displayName } = useLanguage()

const buildings = ref<EventItem[]>([])
const units = ref<UnitLifecycle[]>([])
const tech = ref<TechTiming[]>([])
const timeline = ref<EventItem[]>([])
let dragUnlisten: (() => void) | null = null

const time = ref(0)
const playing = ref(false)
const speed = ref(1)
const countMode = ref<'cumulative' | 'alive'>('cumulative')
const error = ref('')
const backendStarting = ref(true)

const importPath = ref('')
const importJob = ref<ImportJob | null>(null)
const importing = ref(false)
let importTimer: ReturnType<typeof setTimeout> | null = null

const isDesktop = isTauriRuntime()
const overlayEnabled = ref(false)
const overlayOpacity = ref(Number(localStorage.getItem('sc2-overlay-opacity-v3') || 0.55))
const overlayAnchor = ref<OverlayAnchor>(
  savedAnchor('sc2-overlay-anchor', 'top-center'),
)
const overlayMonitor = ref(Number(localStorage.getItem('sc2-overlay-monitor') ?? -1))
const voiceIncludeWorkers = ref(localStorage.getItem('sc2-voice-include-workers') === '1')
const overlaySettingsOpen = ref(false)
const overlaySettingsRef = ref<HTMLElement | null>(null)
const monitors = ref<OverlayMonitor[]>([])
const overlayError = ref('')
let overlayUnlisten: (() => void) | null = null
let overlayShortcutUnregister: (() => Promise<void>) | null = null
let overlaySyncTimer: number | null = null

const {
  rate: voiceRate,
  lang: voiceLang,
  loadDisplaySteps,
  start: voiceStart,
  stop: voiceStop,
  sync: voiceSync,
} = useVoiceReader()
voiceRate.value = Number(localStorage.getItem('sc2-voice-rate') || 1.2)

watch(
  english,
  (value) => {
    voiceLang.value = value ? 'en-US' : 'zh-CN'
    if (overlayEnabled.value) {
      refreshVoiceSteps()
      voiceStart()
      syncVoiceToTimeline()
    }
  },
  { immediate: true },
)

watch(voiceRate, (value) => {
  localStorage.setItem('sc2-voice-rate', String(value))
})

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
const orders = computed(() => timeline.value.filter((event) => event.kind === 'order'))

/** Players shown by the split view, or just the selected player. */
const visiblePlayers = computed<PlayerInfo[]>(() => {
  const players = activeGame.value?.players || []
  if (splitView.value && players.length >= 2) return players.slice(0, 2)
  const current = selectedPlayer.value
  return current ? [current] : []
})

interface ProductionTask {
  key: string
  name: string
  icon: string
  start: number
  done: number | null
}

const UNIT_SECONDS: Record<string, number> = {
  Probe: 12,
  SCV: 12,
  Drone: 12,
  Interceptor: 9,
  Zergling: 17,
  Baneling: 14,
  Roach: 19,
  Ravager: 12,
  Hydralisk: 24,
  Lurker: 18,
  Mutalisk: 24,
  Corruptor: 29,
  BroodLord: 24,
  Overseer: 12,
  Queen: 36,
  Overlord: 18,
  Marine: 18,
  Marauder: 21,
  Reaper: 23,
  Ghost: 29,
  Zealot: 27,
  Stalker: 30,
  Sentry: 23,
  Adept: 27,
  HighTemplar: 32,
  DarkTemplar: 32,
  Immortal: 39,
  Colossus: 48,
  Disruptor: 39,
  Observer: 21,
  WarpPrism: 36,
  Phoenix: 25,
  VoidRay: 36,
  Oracle: 37,
  Tempest: 43,
  Carrier: 64,
  Mothership: 89,
  Hellion: 21,
  Hellbat: 21,
  WidowMine: 21,
  Cyclone: 25,
  SiegeTank: 32,
  Thor: 43,
  Viking: 24,
  Medivac: 30,
  Liberator: 30,
  Raven: 43,
  Banshee: 43,
  Battlecruiser: 64,
}
const DEFAULT_UNIT_SECONDS = 15
const MORPH_SECONDS: Record<string, number> = {
  Baneling: 14,
  Ravager: 12,
  Lurker: 18,
  BroodLord: 24,
  Overseer: 12,
}

const unitProductionTasks = computed(() => {
  const starts = new Map<number, number>()
  for (const event of timeline.value) {
    if (event.kind !== 'unit_training_start') continue
    const unitId = Number(event.payload?.unit_id)
    if (Number.isFinite(unitId)) starts.set(unitId, event.t_sec)
  }

  const result = new Map<number, ProductionTask[]>()
  for (const unit of units.value) {
    if (unit.is_building) continue
    const item = resolveItem(unit.first_type)
    if (!item || item.kind !== 'unit') continue
    if (AUTO_SPAWNED_UNITS.has(item.key) && item.key !== 'Interceptor') continue
    if (AUTO_SPAWNED_UNITS.has(unit.first_type) && unit.first_type !== 'Interceptor') continue
    const fallback = UNIT_SECONDS[item.key] ?? DEFAULT_UNIT_SECONDS
    const start = starts.get(unit.unit_id) ?? Math.max(0, unit.born_t_sec - fallback)
    const tasks = result.get(unit.player_id) || []
    tasks.push({
      key: item.key,
      name: displayName(item, unit.first_type),
      icon: itemIconUrl(item),
      start,
      done: unit.born_t_sec,
    })
    result.set(unit.player_id, tasks)
  }
  return result
})

const morphProductionTasks = computed(() => {
  const result = new Map<number, ProductionTask[]>()
  for (const unit of units.value) {
    if (unit.is_building) continue
    let previous = ''
    for (const morph of unit.morphs) {
      if (morph.from === morph.to) continue
      const seconds = MORPH_SECONDS[morph.to]
      if (!seconds) continue
      const item = resolveItem(morph.to)
      if (!item || item.kind !== 'unit') continue
      const signature = `${item.key}:${morph.t_sec}`
      if (signature === previous) continue
      previous = signature
      const tasks = result.get(unit.player_id) || []
      tasks.push({
        key: item.key,
        name: displayName(item, morph.to),
        icon: itemIconUrl(item),
        start: Math.max(0, morph.t_sec - seconds),
        done: morph.t_sec,
      })
      result.set(unit.player_id, tasks)
    }
  }
  return result
})

function constructionGroupsFor(playerId: number): ConstructionGroupView[] {
  const now = time.value
  const groups = new Map<
    string,
    {
      key: string
      name: string
      icon: string
      count: number
      maxProgress: number
      indeterminate: boolean
      start: number
    }
  >()

  const add = (task: {
    key: string
    name: string
    icon: string
    start: number
    progress: number
    indeterminate: boolean
  }) => {
    const group = groups.get(task.key) || {
      key: task.key,
      name: task.name,
      icon: task.icon,
      count: 0,
      maxProgress: 0,
      indeterminate: false,
      start: task.start,
    }
    group.count += 1
    group.maxProgress = Math.max(group.maxProgress, task.progress)
    group.indeterminate = group.indeterminate || task.indeterminate
    group.start = Math.min(group.start, task.start)
    groups.set(task.key, group)
  }

  const buildingTasks = new Map<number, { name: string; start: number; done?: number }>()
  for (const event of buildings.value) {
    if (event.player_id !== playerId) continue
    const unitId = Number(event.payload?.unit_id)
    if (!Number.isFinite(unitId)) continue
    if (event.kind === 'build_start') {
      buildingTasks.set(unitId, { name: event.name, start: event.t_sec })
    } else if (event.kind === 'build_done' || event.kind === 'unit_born') {
      const task = buildingTasks.get(unitId)
      if (task && task.done === undefined) task.done = event.t_sec
    } else if (event.kind === 'unit_died' && event.t_sec <= now) {
      buildingTasks.delete(unitId)
    }
  }

  for (const task of buildingTasks.values()) {
    if (task.start > now) continue
    if (task.done !== undefined && task.done <= now) continue
    const item = resolveItem(task.name)
    if (!item) continue
    if (item.kind !== 'building' && item.kind !== 'unit') continue
    if (AUTO_SPAWNED_UNITS.has(item.key) && item.key !== 'Interceptor') continue
    const progress =
      task.done !== undefined && task.done > task.start
        ? Math.min(1, Math.max(0, (now - task.start) / (task.done - task.start)))
        : 0
    add({
      key: item.key,
      name: displayName(item, task.name),
      icon: itemIconUrl(item),
      start: task.start,
      progress,
      indeterminate: task.done === undefined,
    })
  }

  const addProductionTask = (task: ProductionTask) => {
    if (task.start > now) return
    if (task.done !== null && task.done <= now) return
    const progress =
      task.done !== null && task.done > task.start
        ? Math.min(1, Math.max(0, (now - task.start) / (task.done - task.start)))
        : 0
    add({
      key: task.key,
      name: task.name,
      icon: task.icon,
      start: task.start,
      progress,
      indeterminate: task.done === null,
    })
  }

  for (const task of unitProductionTasks.value.get(playerId) || []) {
    addProductionTask(task)
  }
  for (const task of morphProductionTasks.value.get(playerId) || []) {
    addProductionTask(task)
  }

  return Array.from(groups.values())
    .sort((a, b) => a.start - b.start)
    .map((group) => ({
      key: group.key,
      name: group.name,
      icon: group.icon,
      count: group.count,
      progress: group.maxProgress,
      indeterminate: group.indeterminate,
    }))
}

const constructionStrips = computed<ConstructionStripView[]>(() => {
  const players = visiblePlayers.value
  return players.map((player, index) => ({
    key: `${player.id}`,
    playerName: player.name,
    race: raceFromName(player.race) || undefined,
    tint: players.length > 1 ? (index === 0 ? 'red' : 'blue') : null,
    groups: constructionGroupsFor(player.id),
  }))
})

function productionTasksFor(playerId: number): ProductionTaskView[] {
  return [
    ...(unitProductionTasks.value.get(playerId) || []),
    ...(morphProductionTasks.value.get(playerId) || []),
  ]
}

const upgradeRows = computed<UpgradeStripRow[]>(() => {
  const players = visiblePlayers.value
  return players.map((player, index) => ({
    key: `${player.id}`,
    playerName: players.length > 1 ? player.name : '',
    tint: players.length > 1 ? (index === 0 ? 'red' : 'blue') : null,
    race: raceFromName(player.race) || 'P',
    tech: tech.value.filter((timing) => timing.player_id === player.id),
    orders: orders.value.filter(
      (event) => event.player_id === player.id && event.kind === 'order',
    ),
  }))
})

function handleOverlaySettingsOutside(event: MouseEvent) {
  if (!overlaySettingsOpen.value) return
  if (overlaySettingsRef.value?.contains(event.target as Node)) return
  overlaySettingsOpen.value = false
}

function handleOverlaySettingsKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') overlaySettingsOpen.value = false
}

onMounted(() => {
  loadFolders()
  document.addEventListener('click', handleOverlaySettingsOutside)
  document.addEventListener('keydown', handleOverlaySettingsKeydown)
  window.addEventListener('resize', handleViewport)
  handleViewport()
  if (isDesktop) {
    void listMonitors().then((items) => {
      monitors.value = items
    })
    void listenDragDrop((paths) => {
      void handleDropPaths(paths)
    })
      .then((unlisten) => {
        dragUnlisten = unlisten
      })
      .catch((exc) => {
        error.value = exc instanceof Error ? exc.message : String(exc)
      })
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
        overlayError.value = ''
      })
      .catch((exc) => {
        overlayError.value = exc instanceof Error ? exc.message : String(exc)
      })
  }
})

onBeforeUnmount(() => {
  pause()
  closeVoice()
  document.removeEventListener('click', handleOverlaySettingsOutside)
  document.removeEventListener('keydown', handleOverlaySettingsKeydown)
  window.removeEventListener('resize', handleViewport)
  dragUnlisten?.()
  if (importTimer) clearTimeout(importTimer)
  if (overlaySyncTimer) clearTimeout(overlaySyncTimer)
  overlayUnlisten?.()
  void overlayShortcutUnregister?.()
  void closeOverlayWindow()
})

watch([time, countMode, activeGameId, activePlayerId], () => {
  if (overlayEnabled.value) scheduleOverlaySync()
})

watch(english, () => {
  if (overlayEnabled.value) scheduleOverlaySync(true)
})

watch(overlayOpacity, (value) => {
  localStorage.setItem('sc2-overlay-opacity-v3', String(value))
  if (overlayEnabled.value) scheduleOverlaySync(true)
})

watch(overlayAnchor, (anchor) => {
  localStorage.setItem('sc2-overlay-anchor', anchor)
  if (overlayEnabled.value) void positionOverlayWindow(anchor, overlayMonitor.value)
})

watch(overlayMonitor, (index) => {
  localStorage.setItem('sc2-overlay-monitor', String(index))
  if (overlayEnabled.value) void positionOverlayWindow(overlayAnchor.value, index)
})

watch(voiceIncludeWorkers, (includeWorkers) => {
  localStorage.setItem('sc2-voice-include-workers', includeWorkers ? '1' : '0')
  if (!overlayEnabled.value) return
  scheduleOverlaySync(true)
  refreshVoiceSteps()
  voiceStart()
  syncVoiceToTimeline()
})

watch(time, () => {
  if (!overlayEnabled.value) return
  syncVoiceToTimeline(playing.value)
})

async function loadFolders() {
  try {
    error.value = ''
    await waitForBackend()
    folders.value = await api.folders()
    if (activeFolderId.value === null && folders.value.length) {
      await selectFolder(folders.value[0])
    } else if (activeFolderId.value !== null) {
      await loadGames(activeFolderId.value)
    }
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : String(exc)
  }
}

async function waitForBackend(timeoutMs = 180_000): Promise<void> {
  backendStarting.value = true
  const deadline = Date.now() + timeoutMs
  let delay = 400
  let lastError: unknown = null
  while (Date.now() < deadline) {
    try {
      await api.health()
      backendStarting.value = false
      return
    } catch (exc) {
      lastError = exc
      await new Promise((resolve) => setTimeout(resolve, delay))
      delay = Math.min(delay * 1.5, 3000)
    }
  }
  backendStarting.value = false
  const detail = lastError instanceof Error ? lastError.message : String(lastError)
  throw new Error(
    english.value
      ? `Backend did not start in time: ${detail}`
      : `后端启动超时：${detail}`,
  )
}

async function selectFolder(folder: FolderInfo) {
  activeFolderId.value = folder.id
  activeGameId.value = null
  activeGame.value = null
  activePlayerId.value = null
  pause()
  closeVoice()
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
    const [detail, buildingEvents, unitRows, techRows, timelineRows] = await Promise.all([
      api.game(game.game_id),
      api.buildings(game.game_id),
      api.units(game.game_id),
      api.tech(game.game_id),
      api.timeline(game.game_id),
    ])
    activeGame.value = detail
    buildings.value = buildingEvents
    units.value = unitRows
    tech.value = techRows
    timeline.value = timelineRows
    activePlayerId.value = detail.players[0]?.id || null
    splitView.value = detail.players.length >= 2 && window.innerWidth >= 1100
    sidebarCollapsed.value = true
    closeVoice()
    if (overlayEnabled.value) enableVoice(true)
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : String(exc)
  }
}

function selectPlayer(playerId: number) {
  activePlayerId.value = playerId
  if (overlayEnabled.value) {
    enableVoice(true)
  }
}

watch(sidebarCollapsed, (collapsed) => {
  localStorage.setItem('sc2-sidebar-collapsed', collapsed ? '1' : '0')
})

function handleViewport() {
  if (window.innerWidth < 1100) splitView.value = false
}

function backToLibrary() {
  pause()
  closeVoice()
  sidebarCollapsed.value = false
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

function raceLetter(raceName: string | null): string {
  return raceFromName(raceName) || '?'
}

async function chooseReplay() {
  try {
    const selected = await pickReplayFile()
    if (selected) await importSingleFile(selected)
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : String(exc)
  }
}

async function handleDropPaths(paths: string[]) {
  const first = paths[0]
  if (!first) return
  if (first.toLowerCase().endsWith(".sc2replay")) {
    await importSingleFile(first)
  } else {
    importPath.value = first
    await startImport()
  }
}

async function importSingleFile(path: string) {
  if (importing.value) return
  importing.value = true
  error.value = ""
  try {
    const result = await api.importFile(path)
    folders.value = await api.folders()
    activeFolderId.value = result.folder_id
    await loadGames(result.folder_id)
    const replay = replays.value.find((item) => item.game_id === result.game_id)
    if (replay) await selectGame(replay)
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : String(exc)
  } finally {
    importing.value = false
  }
}

async function removeFolder(folder: FolderInfo) {
  if (!window.confirm(`删除文件夹「${folder.name}」及其中全部对局？`)) return
  try {
    await api.deleteFolder(folder.id)
    if (activeFolderId.value === folder.id) {
      activeFolderId.value = null
      activeGameId.value = null
      activeGame.value = null
      activePlayerId.value = null
      replays.value = []
      pause()
      closeVoice()
    }
    await loadFolders()
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : String(exc)
  }
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
    english: english.value,
    includeWorkers: voiceIncludeWorkers.value,
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
      closeVoice()
      return
    }
    monitors.value = await listMonitors()
    await openOverlayWindow(overlayAnchor.value, overlayMonitor.value)
    overlayEnabled.value = true
    scheduleOverlaySync(true)
    enableVoice(true)
  } catch (exc) {
    overlayError.value = exc instanceof Error ? exc.message : String(exc)
  }
}

function refreshVoiceSteps() {
  const player = selectedPlayer.value
  if (!player) return

  const orders = timeline.value
    .filter((event) => {
      if (event.player_id !== player.id || event.kind !== 'order') {
        return false
      }
      if (!voiceIncludeWorkers.value && event.is_worker) {
        return false
      }
      const item = resolveItem(event.name)
      if (AUTO_SPAWNED_UNITS.has(event.name)) return false
      if (item && AUTO_SPAWNED_UNITS.has(item.key)) return false
      return true
    })
    .sort((a, b) => a.t_sec - b.t_sec)

  const mergeWindow = 4
  const groups: {
    key: string
    name: string
    time: number
    lastTime: number
    count: number
  }[] = []
  const latest = new Map<string, (typeof groups)[number]>()

  for (const event of orders) {
    const item = resolveItem(event.name)
    const key = item?.key || event.name
    const name = displayName(item, event.name)
    const previous = latest.get(key)
    if (previous && event.t_sec - previous.lastTime <= mergeWindow) {
      previous.count += 1
      previous.lastTime = event.t_sec
      continue
    }
    const group = { key, name, time: event.t_sec, lastTime: event.t_sec, count: 1 }
    groups.push(group)
    latest.set(key, group)
  }

  const items = groups.map((group) => ({
    time: group.time,
    text: group.count > 1 ? `${group.name} ×${group.count}` : group.name,
    speech:
      group.count > 1
        ? english.value
          ? `${group.count} ${group.name}`
          : `${group.name} ${group.count}个`
        : group.name,
  }))
  loadDisplaySteps(items)
}

function syncVoiceToTimeline(speak = playing.value) {
  voiceSync(time.value * SC2_FASTER_REAL_FACTOR, { speak })
}

function enableVoice(autoplay = false) {
  if (!selectedPlayer.value) return
  refreshVoiceSteps()
  voiceStart()
  if (autoplay) syncVoiceToTimeline(playing.value)
}

function closeVoice() {
  voiceStop()
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
  position: relative;
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
  overflow: hidden;
  border-right: 1px solid #142238;
  background:
    linear-gradient(180deg, rgba(17, 31, 53, 0.9), rgba(5, 9, 17, 0.98)),
    #070b14;
  transition: width 180ms ease;
}

.sidebar.collapsed {
  width: 0;
  border-right: 0;
}

.sidebar-inner {
  display: flex;
  flex-direction: column;
  flex: 1;
  width: 310px;
  min-height: 0;
}

.sidebar-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 10px 8px 14px;
  border-bottom: 1px solid #101d2f;
  color: #6f89ad;
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  cursor: pointer;
  user-select: none;
}

.sidebar-bar:hover {
  color: #a8c2e0;
}

.sidebar-bar-title {
  overflow: hidden;
  white-space: nowrap;
}

.collapse-button {
  flex: none;
  height: 22px;
  line-height: 1;
}

.collapse-button:hover {
  color: #dbe9fb;
  border-color: #2f6caf;
}

.sidebar-expand {
  position: absolute;
  left: 0;
  top: 50%;
  z-index: 6;
  width: 16px;
  height: 64px;
  padding: 0;
  transform: translateY(-50%);
  border: 1px solid #1d3352;
  border-left: 0;
  border-radius: 0 8px 8px 0;
  background: rgba(11, 20, 36, 0.94);
  color: #7fa8d8;
  font-size: 12px;
  cursor: pointer;
}

.sidebar-expand:hover {
  color: #eaf4ff;
  border-color: #2f6caf;
  background: #0e1d30;
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
  gap: 6px;
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
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.folder-count {
  flex: none;
  min-width: 18px;
  margin-left: auto;
  color: #5f7d9f;
  font-size: 11px;
  text-align: right;
}

.folder-delete {
  flex: none;
  width: 18px;
  height: 18px;
  padding: 0;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: #4f6b8c;
  font-size: 14px;
  line-height: 16px;
  cursor: pointer;
  opacity: 0;
}

.folder-row:hover .folder-delete,
.folder-row.active .folder-delete {
  opacity: 1;
}

.folder-delete:hover {
  background: rgba(248, 81, 73, 0.18);
  color: #ff8c8c;
}

.import-section {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.import-buttons {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-button {
  padding: 7px 10px;
  font-size: 11px;
}

.import-hint {
  color: #4f6b8c;
  font-size: 10px;
  line-height: 1.4;
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

.backend-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 22px;
  border-bottom: 1px solid #101d2f;
  color: #8fb7df;
  font-size: 12px;
  background: #0a1524;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #63b3ff;
  animation: status-pulse 1.1s ease-in-out infinite;
}

@keyframes status-pulse {
  0%,
  100% {
    opacity: 0.25;
  }
  50% {
    opacity: 1;
  }
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
  align-items: center;
  gap: 10px;
  min-height: 48px;
  padding: 7px 22px;
  overflow: hidden;
  border-bottom: 1px solid #101d2f;
  background: rgba(7, 12, 22, 0.9);
  white-space: nowrap;
}

.back-button {
  flex: none;
  padding: 4px 9px;
  border: 1px solid #1d3352;
  border-radius: 6px;
  background: #080f1c;
  color: #7f9ab9;
  font-size: 11px;
  cursor: pointer;
}

.back-button:hover {
  border-color: #3d7fc4;
  color: #e8f4ff;
}

.header-folder {
  flex: 0 1 auto;
  max-width: 120px;
  overflow: hidden;
  color: #5f7d9f;
  font-size: 10px;
  letter-spacing: 0.08em;
  text-overflow: ellipsis;
  text-transform: uppercase;
}

.header-map {
  flex: 0 1 auto;
  min-width: 0;
  max-width: 260px;
  margin: 0;
  overflow: hidden;
  font-size: 18px;
  line-height: 1.2;
  text-overflow: ellipsis;
  background: linear-gradient(90deg, #dcecff, #7fb9ff);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.player-tabs {
  display: flex;
  flex: none;
  align-items: center;
  gap: 5px;
  min-width: 0;
}

.versus {
  flex: none;
  color: #55708f;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.player-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  max-width: 150px;
  min-width: 0;
  padding: 4px 8px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: transparent;
  color: #8fa9c7;
  font-size: 12px;
  cursor: pointer;
}

.player-tab:hover {
  border-color: #1d3352;
  background: #0c1728;
  color: #dbe9fb;
}

.player-tab.active {
  border-color: #3d7fc4;
  background: #0e1d30;
  color: #e8f3ff;
  box-shadow: 0 0 10px rgba(61, 127, 196, 0.2);
}

.player-tab-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.player-tab.winner .crown {
  color: #e5bd5f;
}

.header-metrics {
  display: flex;
  flex: none;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.split-switch {
  display: flex;
  flex: none;
  align-items: center;
  gap: 6px;
  padding: 3px 8px 3px 4px;
  border: 1px solid #1d3352;
  border-radius: 6px;
  background: #080f1c;
  color: #6f89ad;
  font-size: 10px;
  cursor: pointer;
}

.split-switch:hover {
  border-color: #2f5f96;
  color: #b8d2ef;
}

.split-switch.active {
  border-color: #3d7fc4;
  background: #102540;
  color: #d8ebff;
}

.split-switch-track {
  position: relative;
  display: block;
  width: 26px;
  height: 14px;
  border-radius: 999px;
  background: #16263d;
  transition: background 160ms ease;
}

.split-switch-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #6f89ad;
  transition: transform 160ms ease, background 160ms ease;
}

.split-switch.active .split-switch-track {
  background: #245a94;
}

.split-switch.active .split-switch-knob {
  transform: translateX(12px);
  background: #eaf4ff;
}

@media (max-width: 1250px) {
  .header-folder {
    display: none;
  }
}

@media (max-width: 1100px) {
  .header-map {
    max-width: 150px;
  }
}

.voice-toggle {
  padding: 7px 10px;
  border: 1px solid #1d3352;
  border-radius: 8px;
  background: #080f1c;
  color: #8ca6c8;
  font-size: 11px;
  cursor: pointer;
}

.voice-toggle.active {
  border-color: #a855f7;
  background: rgba(168, 85, 247, 0.16);
  color: #d8b4fe;
}

.race-icon {
  display: grid;
  flex: none;
  width: 18px;
  height: 18px;
  place-items: center;
  border-radius: 4px;
  background: #6f89ad;
  color: #07101c;
  font-size: 9px;
  font-weight: 800;
  line-height: 1;
}

.race-icon.p {
  background: #69db7c;
  box-shadow: 0 0 7px rgba(105, 219, 124, 0.5);
}

.race-icon.t {
  background: #74c0fc;
  box-shadow: 0 0 7px rgba(116, 192, 252, 0.5);
}

.race-icon.z {
  background: #b197fc;
  box-shadow: 0 0 7px rgba(177, 151, 252, 0.5);
}

.tree-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 8px 22px;
  border-bottom: 1px solid #0e1a2b;
  background: rgba(6, 11, 20, 0.65);
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

.overlay-settings-picker {
  position: relative;
}

.overlay-settings-button {
  padding: 4px 9px;
  border: 1px solid #1d3352;
  border-radius: 7px;
  background: transparent;
  color: #7893b5;
  font-size: 11px;
  cursor: pointer;
}

.overlay-settings-button:hover,
.overlay-settings-button.active {
  border-color: #3d7fc4;
  color: #d9ecff;
}

.overlay-settings-panel {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 50;
  width: 270px;
  padding: 8px 10px;
  border: 1px solid #24466f;
  border-radius: 8px;
  background: #08111f;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
}

.overlay-setting-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 6px 0;
  color: #9fb8d8;
  font-size: 10px;
}

.overlay-setting-row + .overlay-setting-row {
  border-top: 1px solid #162a45;
}

.overlay-setting-row > span {
  width: 58px;
  color: #7ca5cf;
}

.overlay-setting-row b {
  margin-left: auto;
  color: #cfe3fa;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 10px;
}

.overlay-setting-row input[type='range'] {
  width: 100%;
  accent-color: #4b9bf0;
}

.overlay-setting-check {
  margin-left: auto;
  width: 14px;
  height: 14px;
  accent-color: #a855f7;
}

.overlay-setting-row select {
  flex: 1;
  min-width: 0;
  padding: 3px 5px;
  border: 1px solid #1d3352;
  border-radius: 5px;
  background: #070d18;
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

</style>
