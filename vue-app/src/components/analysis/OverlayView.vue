<template>
  <div class="overlay-root" :style="{ '--panel-alpha': state?.opacity ?? 0.78 }">
    <div class="overlay-panel">
      <header class="overlay-header">
        <div class="playing">
          <span class="label">Currently playing</span>
          <span class="player">{{ state?.playerName || '—' }}</span>
          <span v-if="state?.race" class="race">{{ state.race }}</span>
        </div>
        <div class="clock">{{ formatClock(state?.time || 0) }}</div>
      </header>

      <div class="build-strip">
        <template v-for="(row, index) in buildRows" :key="row.key">
          <span v-if="index > 0" class="arrow">»</span>
          <div class="build-item" :class="{ past: row.past, next: row.next }">
            <img :src="iconUrl(row.item.abbr)" :alt="row.item.name" draggable="false" />
            <span class="build-name">{{ row.item.nameZh }}</span>
            <span class="build-time">{{ formatClock(row.event.t_sec) }}</span>
          </div>
        </template>
        <div v-if="buildRows.length === 0" class="empty">等待建造</div>
      </div>

      <div class="mini-tree">
        <div class="mini-label">
          <span>后续解锁</span>
          <span class="mini-sub">60s 高亮</span>
        </div>
        <div class="mini-chain">
          <template v-for="(entry, index) in previewUnlocks" :key="`${entry.item.key}-${entry.event.t_sec}`">
            <span v-if="index > 0" class="mini-arrow">›</span>
            <div class="mini-item" :title="`${entry.item.nameZh} ${formatClock(entry.event.t_sec)}`">
              <img :src="itemIconUrl(entry.item)" :alt="entry.item.name" draggable="false" />
              <span class="mini-time" :class="{ soon: isSoon(entry.event.t_sec) }">
                {{ formatClock(entry.event.t_sec) }}
              </span>
            </div>
          </template>
          <span v-if="overflowUnlocks > 0" class="mini-overflow">+{{ overflowUnlocks }}</span>
          <div v-if="previewUnlocks.length === 0" class="mini-empty">暂无新的解锁</div>
        </div>
      </div>

      <div v-if="!state" class="waiting">
        <div class="waiting-title">等待主窗口</div>
        <div class="waiting-subtitle">打开一场对局并启用 Overlay</div>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { api } from '../../api'
import { formatClock, iconUrl, itemIconUrl, resolveItem, type CatalogItem } from '../../data/catalog'
import type { EventItem, OverlayState } from '../../types-analysis'
import { emitOverlayReady, isTauriRuntime, listenOverlayEvent } from '../../composables/useTauri'

const state = ref<OverlayState | null>(null)
const events = ref<EventItem[]>([])
const error = ref('')
let unlisten: (() => void) | null = null
let loadedKey = ''
let loading = false

const buildActions = computed(() =>
  events.value
    .filter((event) => event.kind === 'order' && !event.is_worker && resolveItem(event.name))
    .sort((a, b) => a.t_sec - b.t_sec),
)

interface BuildRow {
  key: string
  event: EventItem
  item: CatalogItem
  past: boolean
  next: boolean
}

const buildRows = computed<BuildRow[]>(() => {
  const time = state.value?.time ?? 0
  const actions = buildActions.value
  const past = actions.filter((event) => event.t_sec <= time).slice(-1)
  const upcoming = actions.filter((event) => event.t_sec > time).slice(0, past.length ? 3 : 4)
  const selected = [...past, ...upcoming]
  return selected.map((event, index) => ({
    key: `${event.kind}:${event.name}:${event.t_sec}:${index}`,
    event,
    item: resolveItem(event.name)!,
    past: event.t_sec <= time,
    next: index === past.length,
  }))
})

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
    const isUnitBorn =
      event.kind === 'unit_born' &&
      !event.is_worker &&
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

const previewUnlocks = computed(() => futureUnlocks.value.slice(0, 16))
const overflowUnlocks = computed(() => Math.max(0, futureUnlocks.value.length - previewUnlocks.value.length))

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
  padding: 6px;
  box-sizing: border-box;
  pointer-events: none;
  user-select: none;
  font-family: 'Noto Sans SC', 'Segoe UI', sans-serif;
}

.overlay-panel {
  position: relative;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  padding: 9px 13px 10px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  overflow: hidden;
  border: 1px solid rgba(73, 143, 220, 0.45);
  border-radius: 10px;
  background: rgba(4, 9, 18, var(--panel-alpha, 0.78));
  box-shadow: 0 8px 26px rgba(0, 0, 0, 0.45), inset 0 0 22px rgba(61, 127, 196, 0.08);
  backdrop-filter: blur(5px);
}

.overlay-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.playing {
  display: flex;
  align-items: baseline;
  gap: 7px;
  min-width: 0;
}

.label {
  color: #6f89ad;
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  flex: none;
}

.player {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #e8f4ff;
  font-size: 16px;
  font-weight: 700;
}

.race {
  flex: none;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(61, 127, 196, 0.25);
  color: #9fc3ef;
  font-size: 9px;
}

.clock {
  flex: none;
  color: #e8f4ff;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-shadow: 0 0 14px rgba(90, 167, 237, 0.5);
}

.build-strip {
  display: flex;
  align-items: center;
  gap: 7px;
  min-height: 70px;
}

.build-item {
  flex: 0 1 92px;
  min-width: 72px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 4px 3px;
  border-radius: 7px;
  border: 1px solid transparent;
  color: #cfe3fa;
}

.build-item.past {
  opacity: 0.4;
}

.build-item.next {
  border-color: rgba(90, 167, 237, 0.45);
  background: rgba(61, 127, 196, 0.14);
}

.build-item img {
  width: 48px;
  height: 48px;
  object-fit: contain;
  border-radius: 6px;
  border: 1px solid #2c5480;
  background: #0b1424;
}

.build-name {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  line-height: 1.2;
}

.build-time {
  color: #7f99bb;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 10px;
}

.arrow {
  flex: none;
  color: #4b9bf0;
  font-size: 26px;
  font-weight: 800;
  line-height: 1;
  opacity: 0.8;
}

.mini-tree {
  display: flex;
  align-items: center;
  gap: 9px;
  min-height: 56px;
  padding-top: 6px;
  border-top: 1px solid rgba(73, 143, 220, 0.2);
}

.mini-label {
  flex: none;
  width: 48px;
  display: flex;
  flex-direction: column;
  color: #8ca6c8;
  font-size: 10px;
  line-height: 1.25;
}

.mini-sub {
  color: #5f7d9f;
  letter-spacing: 0.12em;
}

.mini-chain {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  overflow: hidden;
}

.mini-item {
  flex: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
}

.mini-item img {
  width: 32px;
  height: 32px;
  object-fit: contain;
  border-radius: 5px;
  border: 1px solid #2c5480;
  background: #0b1424;
}

.mini-time {
  color: #4f6b8c;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 9px;
}

.mini-time.soon {
  color: #e8f4ff;
  font-weight: 700;
  text-shadow: 0 0 8px rgba(90, 167, 237, 0.75);
}

.mini-overflow {
  margin-left: 3px;
  color: #8ca6c8;
  font-size: 10px;
}

.mini-arrow {
  flex: none;
  color: #3d7fc4;
  font-size: 16px;
}

.empty,
.mini-empty {
  color: #5f7d9f;
  font-size: 11px;
  font-style: italic;
  padding: 4px;
}

.waiting {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  text-align: center;
  background: rgba(4, 9, 18, 0.92);
  border-radius: 10px;
}

.waiting-title {
  color: #dcecff;
  font-size: 18px;
}

.waiting-subtitle {
  margin-top: 4px;
  color: #6f89ad;
  font-size: 11px;
}

.error {
  position: absolute;
  right: 10px;
  bottom: 8px;
  max-width: 70%;
  padding: 4px 7px;
  border-radius: 5px;
  background: rgba(80, 20, 20, 0.85);
  color: #ffb4b4;
  font-size: 10px;
}
</style>
