<template>
  <div class="overlay-root" :style="{ '--panel-alpha': state?.opacity ?? 0.6 }">
    <div class="overlay-panel">
      <!-- Top Line: Time + Player + Next Action Highlight -->
      <div class="overlay-top">
        <div class="player-block">
          <span class="clock">{{ formatClock(state?.time || 0) }}</span>
          <span class="player-name">{{ state?.playerName || '—' }}</span>
          <span v-if="state?.race" class="race-tag">{{ state.race }}</span>
        </div>

        <div class="build-summary">
          <span class="build-summary-label">建造中</span>
          <div v-if="activeBuilds.length" class="build-summary-items">
            <div
              v-for="build in visibleBuilds"
              :key="build.key"
              class="build-summary-item"
              :title="`${displayName(build.item)}${build.count > 1 ? ` ×${build.count}` : ''}`"
            >
              <img :src="iconUrl(build.item.abbr)" :alt="build.item.name" draggable="false" />
              <span v-if="build.count > 1" class="build-summary-count">×{{ build.count }}</span>
              <div class="build-summary-bar">
                <div
                  class="build-summary-fill"
                  :class="{ indeterminate: build.indeterminate }"
                  :style="{ width: `${build.progress * 100}%` }"
                />
              </div>
            </div>
            <span v-if="overflowBuilds > 0" class="build-summary-overflow">+{{ overflowBuilds }}</span>
          </div>
          <span v-else class="build-summary-empty">无</span>
        </div>
      </div>

      <!-- Bottom Line: Ticker (Build steps) + Mini Unlocks -->
      <div class="overlay-bottom">
        <div class="build-chain">
          <template v-for="(row, index) in buildRows" :key="row.key">
            <span v-if="index > 0" class="chain-arrow">»</span>
            <div class="chain-item" :class="{ past: row.past, current: row.current }">
              <img :src="iconUrl(row.item.abbr)" :alt="row.item.name" draggable="false" />
              <div class="item-meta">
                <span class="item-name">
                  {{ displayName(row.item) }}
                  <b v-if="row.count > 1" class="item-count">×{{ row.count }}</b>
                </span>
                <span class="item-time">{{ formatClock(row.event.t_sec) }}</span>
              </div>
            </div>
          </template>
          <div v-if="buildRows.length === 0" class="empty-hint">等待建造操作</div>
        </div>

        <div class="chain-divider" />

        <div class="unlock-chain">
          <span class="unlock-label">解锁</span>
          <div class="unlock-items">
            <div
              v-for="entry in previewUnlocks"
              :key="`${entry.item.key}-${entry.event.t_sec}`"
              class="unlock-item"
              :class="{ soon: isSoon(entry.event.t_sec) }"
              :title="`${displayName(entry.item)} ${formatClock(entry.event.t_sec)}`"
            >
              <img :src="itemIconUrl(entry.item)" :alt="entry.item.name" draggable="false" />
              <span class="unlock-time">{{ formatClock(entry.event.t_sec) }}</span>
            </div>
            <span v-if="overflowUnlocks > 0" class="unlock-overflow">+{{ overflowUnlocks }}</span>
          </div>
          <div v-if="previewUnlocks.length === 0" class="empty-hint">暂无后续解锁</div>
        </div>
      </div>

      <div v-if="!state" class="waiting-layer">
        <div class="waiting-title">等待主窗口连接…</div>
      </div>
      <div v-if="error" class="error-badge">{{ error }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { api } from '../../api'
import {
  AUTO_SPAWNED_UNITS,
  WORKER_UNITS,
  formatClock,
  iconUrl,
  itemIconUrl,
  resolveItem,
  type CatalogItem,
} from '../../data/catalog'
import type { EventItem, OverlayState } from '../../types-analysis'
import { emitOverlayReady, isTauriRuntime, listenOverlayEvent } from '../../composables/useTauri'
import { useLanguage } from '../../composables/useLanguage'

const { english, displayName } = useLanguage()
const state = ref<OverlayState | null>(null)
const events = ref<EventItem[]>([])
const error = ref('')
let unlisten: (() => void) | null = null
let loadedKey = ''
let loading = false

const buildGroups = computed(() => {
  const includeWorkers = state.value?.includeWorkers ?? false
  const actions = events.value
    .filter(
      (event) =>
        event.kind === 'order' &&
        (includeWorkers || !event.is_worker) &&
        resolveItem(event.name),
    )
    .sort((a, b) => a.t_sec - b.t_sec)

  const groups: {
    key: string
    event: EventItem
    item: CatalogItem
    count: number
    lastTime: number
  }[] = []
  for (const event of actions) {
    const item = resolveItem(event.name)!
    const last = groups[groups.length - 1]
    if (last && last.item.key === item.key && event.t_sec - last.lastTime <= 4) {
      last.count += 1
      last.lastTime = event.t_sec
      continue
    }
    groups.push({
      key: `${event.kind}:${event.name}:${event.t_sec}`,
      event,
      item,
      count: 1,
      lastTime: event.t_sec,
    })
  }
  return groups
})

interface BuildRow {
  key: string
  event: EventItem
  item: CatalogItem
  count: number
  past: boolean
  current: boolean
}

const buildRows = computed<BuildRow[]>(() => {
  const time = state.value?.time ?? 0
  const groups = buildGroups.value
  const past = groups.filter((group) => group.event.t_sec <= time).slice(-1)
  const upcoming = groups
    .filter((group) => group.event.t_sec > time)
    .slice(0, past.length ? 3 : 4)
  const selected = [...past, ...upcoming]
  return selected.map((group, index) => ({
    key: `${group.key}:${index}`,
    event: group.event,
    item: group.item,
    count: group.count,
    past: group.event.t_sec <= time,
    current: past.length > 0 ? index === past.length - 1 : index === 0,
  }))
})


interface ActiveBuild {
  key: string
  item: CatalogItem
  count: number
  progress: number
  indeterminate: boolean
  start: number
}

const activeBuilds = computed<ActiveBuild[]>(() => {
  const time = state.value?.time ?? 0
  const includeWorkers = state.value?.includeWorkers ?? false
  const tasks = new Map<number, { name: string; start: number; done?: number }>()
  for (const event of events.value) {
    const unitId = Number(event.payload?.unit_id)
    if (!Number.isFinite(unitId)) continue
    if (event.kind === 'build_start' || event.kind === 'unit_training_start') {
      if (!tasks.has(unitId)) tasks.set(unitId, { name: event.name, start: event.t_sec })
    } else if (event.kind === 'build_done' || event.kind === 'unit_born') {
      const task = tasks.get(unitId)
      if (task) task.done = event.t_sec
    }
  }

  const groups = new Map<string, ActiveBuild>()
  for (const task of tasks.values()) {
    if (task.start > time) continue
    if (task.done !== undefined && task.done <= time) continue
    const item = resolveItem(task.name)
    if (!item) continue
    if (!includeWorkers && WORKER_UNITS.has(item.key)) continue
    if (AUTO_SPAWNED_UNITS.has(item.key) && item.key !== 'Interceptor') continue
    const progress =
      task.done !== undefined && task.done > task.start
        ? Math.min(1, Math.max(0, (time - task.start) / (task.done - task.start)))
        : 0
    const current = groups.get(item.key)
    if (current) {
      current.count += 1
      current.progress = Math.max(current.progress, progress)
      current.indeterminate = current.indeterminate || task.done === undefined
      current.start = Math.min(current.start, task.start)
      continue
    }
    groups.set(item.key, {
      key: item.key,
      item,
      count: 1,
      progress,
      indeterminate: task.done === undefined,
      start: task.start,
    })
  }
  return [...groups.values()].sort((left, right) => left.start - right.start)
})

const visibleBuilds = computed(() => activeBuilds.value.slice(0, 4))
const overflowBuilds = computed(() => Math.max(0, activeBuilds.value.length - visibleBuilds.value.length))

interface UnlockEntry {
  event: EventItem
  item: CatalogItem
}

const unlockEntries = computed<UnlockEntry[]>(() => {
  const seen = new Set<string>()
  const result: UnlockEntry[] = []
  const ordered = [...events.value].sort((a, b) => a.t_sec - b.t_sec)

  for (const event of ordered) {
    const isBuildingDone =
      event.kind === 'build_done' ||
      (event.kind === 'unit_born' && event.payload?.is_building === true)
    const isUpgradeDone = event.kind === 'upgrade_done'
    const includeWorkers = state.value?.includeWorkers ?? false
    const isUnitBorn =
      event.kind === 'unit_born' &&
      (includeWorkers || !event.is_worker) &&
      event.payload?.is_building !== true

    if (!isBuildingDone && !isUpgradeDone && !isUnitBorn) continue
    const item = resolveItem(event.name)
    if (!item) continue
    if (item.kind === 'building' && !isBuildingDone) continue
    if (item.kind === 'upgrade' && !isUpgradeDone) continue
    if (item.kind === 'unit' && !isUnitBorn) continue

    const dedupeKey = `${item.kind}:${item.key}`
    if (seen.has(dedupeKey)) continue
    seen.add(dedupeKey)
    result.push({ event, item })
  }
  return result
})

const futureUnlocks = computed(() => {
  const time = state.value?.time ?? 0
  return unlockEntries.value.filter((entry) => entry.event.t_sec > time)
})

const UNLOCK_PREVIEW_COUNT = 5
const previewUnlocks = computed(() => futureUnlocks.value.slice(0, UNLOCK_PREVIEW_COUNT))
const overflowUnlocks = computed(() =>
  Math.max(0, futureUnlocks.value.length - previewUnlocks.value.length),
)

function isSoon(tSec: number): boolean {
  const time = state.value?.time ?? 0
  return tSec <= time + 60
}

onMounted(async () => {
  if (isTauriRuntime()) {
    try {
      const { getCurrentWindow } = await import('@tauri-apps/api/window')
      await getCurrentWindow().setIgnoreCursorEvents(true)
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    }
  }
  unlisten = await listenOverlayEvent<OverlayState>('sc2-overlay-state', (payload) => {
    state.value = payload
    english.value = payload.english
    void loadData()
  })
  await emitOverlayReady()
})

onBeforeUnmount(() => {
  unlisten?.()
})

async function loadData() {
  const current = state.value
  if (!current?.gameId || !current.playerId || loading) return
  const key = `${current.gameId}:${current.playerId}`
  if (loadedKey === key) return

  loading = true
  error.value = ''
  try {
    events.value = await api.timeline(current.gameId, current.playerId)
    loadedKey = key
  } catch (exc) {
    error.value = exc instanceof Error ? exc.message : String(exc)
  } finally {
    loading = false
  }
}
</script>

<style scoped>
.overlay-root {
  position: fixed;
  inset: 0;
  padding: 4px;
  box-sizing: border-box;
  pointer-events: none;
  user-select: none;
  font-family: 'Noto Sans SC', 'Segoe UI', system-ui, sans-serif;
}

.overlay-panel {
  position: relative;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  padding: 6px 12px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  border: 1px solid rgba(73, 143, 220, 0.35);
  border-radius: 8px;
  background: rgba(3, 7, 15, var(--panel-alpha, 0.6));
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(8px);
}

.overlay-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  height: 30px;
}

.player-block {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.clock {
  color: #e8f4ff;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-shadow: 0 0 10px rgba(90, 167, 237, 0.6);
}

.player-name {
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #cfe3fa;
  font-size: 13px;
  font-weight: 600;
}

.race-tag {
  flex: none;
  padding: 1px 5px;
  border-radius: 3px;
  background: rgba(61, 127, 196, 0.28);
  color: #a4ccff;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
}

.build-summary {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  max-width: 330px;
  padding: 2px 6px;
  border: 1px solid rgba(90, 167, 237, 0.28);
  border-radius: 5px;
  background: rgba(75, 155, 240, 0.08);
}

.build-summary-label {
  flex: none;
  color: #8ec5ff;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.build-summary-items {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  overflow: hidden;
}

.build-summary-item {
  position: relative;
  flex: none;
  width: 26px;
  height: 26px;
  overflow: hidden;
  border: 1px solid #1f3a5e;
  border-radius: 4px;
  background: #07101c;
}

.build-summary-item img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.build-summary-count {
  position: absolute;
  right: 1px;
  top: 0;
  color: #ffffff;
  font-size: 9px;
  font-weight: 800;
  line-height: 1;
  text-shadow: 0 0 2px #000, 0 1px 2px #000;
}

.build-summary-bar {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.65);
}

.build-summary-fill {
  height: 100%;
  background: #ffffff;
}

.build-summary-fill.indeterminate {
  width: 35% !important;
  animation: build-summary-pulse 1.2s ease-in-out infinite;
}

.build-summary-overflow,
.build-summary-empty {
  color: #4f6b8c;
  font-size: 9px;
  font-style: italic;
}

@keyframes build-summary-pulse {
  0%,
  100% {
    opacity: 0.35;
  }
  50% {
    opacity: 1;
  }
}

.overlay-bottom {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 52px;
  border-top: 1px solid rgba(73, 143, 220, 0.18);
  padding-top: 4px;
}

.build-chain {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  overflow: hidden;
}

.chain-arrow {
  color: #4b9bf0;
  font-size: 16px;
  font-weight: 800;
  opacity: 0.7;
}

.chain-item {
  flex: 0 1 auto;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 6px;
  border-radius: 5px;
  background: rgba(8, 16, 28, 0.5);
  border: 1px solid transparent;
  min-width: 0;
}

.chain-item.past {
  opacity: 0.42;
}

.chain-item.current {
  opacity: 1;
  border-color: rgba(90, 167, 237, 0.5);
  background: rgba(61, 127, 196, 0.2);
}

.chain-item img {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  object-fit: contain;
  border: 1px solid #1f3a5e;
  background: #081220;
}

.item-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.item-count,
.item-name {
  font-size: 11px;
  font-weight: 600;
  color: #d6e8fc;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-time {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 9px;
  color: #7b99bd;
}

.chain-divider {
  width: 1px;
  height: 38px;
  background: rgba(73, 143, 220, 0.25);
  flex: none;
}

.unlock-chain {
  flex: none;
  display: flex;
  align-items: center;
  gap: 6px;
}

.unlock-label {
  font-size: 10px;
  font-weight: 700;
  color: #7a98bd;
  letter-spacing: 0.1em;
}

.unlock-items {
  display: flex;
  align-items: center;
  gap: 5px;
}

.unlock-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
}

.unlock-item img {
  width: 26px;
  height: 26px;
  border-radius: 4px;
  object-fit: contain;
  border: 1px solid #1a3352;
  background: #07101c;
}

.unlock-time {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 8.5px;
  color: #557294;
}

.unlock-item.soon .unlock-time {
  color: #e8f4ff;
  font-weight: 700;
  text-shadow: 0 0 6px rgba(90, 167, 237, 0.8);
}

.unlock-overflow {
  align-self: center;
  margin-left: 1px;
  color: #7a98bd;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 9px;
  font-weight: 700;
}

.empty-hint {
  font-size: 10px;
  color: #4f6b8c;
  font-style: italic;
  padding: 2px;
}

.waiting-layer {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  background: rgba(4, 9, 18, 0.88);
  border-radius: 8px;
}

.waiting-title {
  color: #9ec5ed;
  font-size: 14px;
  font-weight: 600;
}

.error-badge {
  position: absolute;
  right: 8px;
  bottom: 6px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(120, 20, 20, 0.85);
  color: #ffcccc;
  font-size: 9px;
}

</style>
