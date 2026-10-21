<template>
  <div class="library">
    <header class="library-head">
      <div>
        <div class="eyebrow">Replay Library</div>
        <h2>{{ folderName || '对局列表' }}</h2>
      </div>
      <div class="library-meta">
        <span>
          {{ filteredReplays.length === replays.length ? replays.length : `${filteredReplays.length} / ${replays.length}` }}
          场
        </span>
        <span class="phase-legend">
          <i class="phase-dot early" />前
          <i class="phase-dot mid" />中
          <i class="phase-dot late" />后
        </span>
      </div>
    </header>

    <div v-if="!loading && replays.length" class="library-filters">
      <input
        v-model="filterId"
        class="filter-id"
        placeholder="玩家 ID / 对局 ID"
      />
      <div class="filter-races">
        <button
          :class="{ active: !filterRace }"
          @click="filterRace = null"
        >
          全部
        </button>
        <button
          v-for="race in races"
          :key="race"
          :class="[race.toLowerCase(), { active: filterRace === race }]"
          @click="filterRace = filterRace === race ? null : race"
        >
          {{ race }}
        </button>
      </div>
      <div ref="pickerRef" class="filter-picker">
        <button
          class="filter-picker-button"
          :class="{ active: selectedItems.length }"
          @click="filtersOpen = !filtersOpen"
        >
          <span>筛选兵种 / 科技 / 建筑</span>
          <span v-if="selectedItems.length" class="filter-count-badge">
            {{ selectedItems.length }}
          </span>
          <span class="filter-caret">▾</span>
        </button>

        <div v-if="filtersOpen" class="filter-panel" @click.stop>
          <div class="filter-columns">
            <section v-for="column in filterColumns" :key="column.key" class="filter-column">
              <div class="filter-column-title">{{ column.title }}</div>
              <div class="filter-option-grid">
                <button
                  v-for="item in column.items"
                  :key="item.key"
                  class="filter-option"
                  :class="{ selected: selectedItems.includes(item.key) }"
                  :title="`${displayName(item)} · ${item.race}`"
                  @click="toggleFilterItem(item.key)"
                >
                  <img :src="itemIconUrl(item)" :alt="item.name" draggable="false" />
                </button>
              </div>
            </section>
          </div>
          <footer class="filter-panel-footer">
            <span class="filter-hint">匹配任一已选项</span>
            <button v-if="selectedItems.length" class="filter-panel-clear" @click="selectedItems = []">
              清空
            </button>
            <button class="filter-panel-done" @click="filtersOpen = false">完成</button>
          </footer>
        </div>
      </div>

      <div v-if="selectedItems.length" class="filter-selected">
        <button
          v-for="item in selectedCatalogItems"
          :key="item.key"
          class="filter-selected-chip"
          :title="displayName(item)"
          @click="toggleFilterItem(item.key)"
        >
          <img :src="itemIconUrl(item)" :alt="item.name" draggable="false" />
          <span class="selected-remove">×</span>
        </button>
      </div>
      <button v-if="hasFilters" class="filter-clear" @click="clearFilters">清除</button>
    </div>

    <div v-if="loading" class="library-empty">正在读取对局…</div>
    <div v-else-if="replays.length === 0" class="library-empty">
      这个文件夹还没有导入录像
    </div>
    <div v-else-if="filteredReplays.length === 0" class="library-empty">
      没有符合筛选条件的对局
    </div>

    <div v-else class="replay-list">
      <button
        v-for="replay in filteredReplays"
        :key="replay.game_id"
        class="replay-card"
        @click="$emit('open', replay)"
      >
        <div class="replay-map">
          <div class="map-name">{{ replay.map_name || 'Unknown Map' }}</div>
          <div class="map-meta">
            <span>{{ formatClock(replay.duration_sec || 0) }}</span>
            <span v-if="replay.winner" class="winner">胜 {{ replay.winner }}</span>
          </div>
          <div class="map-file" :title="replay.file_name">{{ replay.file_name }}</div>
        </div>

        <div
          v-for="player in replay.player_details.slice(0, 2)"
          :key="player.id"
          class="player-summary"
        >
          <div class="player-head">
            <span class="race-badge" :class="raceClass(player.race)">
              {{ raceLetter(player.race) }}
            </span>
            <span class="player-name">{{ player.name }}</span>
            <span class="player-result" :class="{ win: player.is_winner }">
              {{ player.is_winner ? 'WIN' : player.result || '—' }}
            </span>
          </div>

          <div class="summary-line units-line">
            <span class="summary-label">兵种</span>
            <div class="chip-row">
              <span
                v-for="unit in unitPreview(player)"
                :key="unit.key"
                class="unit-chip"
                :title="unit.name"
              >
                <img v-if="unit.icon" :src="unit.icon" :alt="unit.name" draggable="false" />
                <span class="chip-count">{{ unit.count }}</span>
              </span>
              <span v-if="unitPreview(player).length === 0" class="none">—</span>
            </div>
          </div>

          <div class="summary-line tech-line">
            <span class="summary-label">科技</span>
            <div class="tech-groups">
              <div v-for="phase in phases" :key="phase.key" class="tech-phase">
                <span class="phase-label" :class="phase.key">{{ phase.short }}</span>
                <div class="tech-icons">
                  <span
                    v-for="tech in phaseTech(player, phase.key)"
                    :key="tech.tech"
                    class="tech-chip"
                    :title="`${techName(tech.tech)} ${formatClock(tech.t_sec)}`"
                  >
                    <img
                      v-if="techIcon(tech.tech)"
                      :src="techIcon(tech.tech)"
                      :alt="techName(tech.tech)"
                      draggable="false"
                    />
                  </span>
                  <span v-if="phaseTech(player, phase.key).length === 0" class="none">—</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { FolderReplay, FolderReplayPlayer, Race } from '../../types-analysis'
import {
  AUTO_SPAWNED_UNITS,
  WORKER_UNITS,
  catalog,
  type CatalogItem,
  formatClock,
  iconUrl,
  itemIconUrl,
  raceFromName,
  resolveItem,
} from '../../data/catalog'
import { useLanguage } from '../../composables/useLanguage'
import { useSettings } from '../../composables/useSettings'

const props = defineProps<{
  replays: FolderReplay[]
  folderName: string
  loading: boolean
}>()

defineEmits<{
  (event: 'open', replay: FolderReplay): void
}>()

const { displayName } = useLanguage()
const { settings } = useSettings()


const races: Race[] = ['P', 'T', 'Z']
const filterId = ref('')
const filterRace = ref<Race | null>(null)
const selectedItems = ref<string[]>([])
const filtersOpen = ref(false)
const pickerRef = ref<HTMLElement | null>(null)

const filterColumns = computed(() => {
  const items = Object.values(catalog).filter(
    (item) =>
      (item.kind === 'unit' || item.kind === 'upgrade' || item.kind === 'building') &&
      (!filterRace.value || item.race === filterRace.value),
  )
  const sort = (left: CatalogItem, right: CatalogItem) =>
    displayName(left).localeCompare(displayName(right), 'zh')
  return [
    { key: 'unit', title: '兵种', items: items.filter((item) => item.kind === 'unit').sort(sort) },
    {
      key: 'tech',
      title: '科技',
      items: items.filter((item) => item.kind === 'upgrade').sort(sort),
    },
    {
      key: 'building',
      title: '建筑',
      items: items.filter((item) => item.kind === 'building').sort(sort),
    },
  ]
})

const selectedCatalogItems = computed(() =>
  selectedItems.value
    .map((key) => catalog[key])
    .filter((item): item is CatalogItem => Boolean(item)),
)

const hasFilters = computed(
  () => Boolean(filterId.value.trim() || filterRace.value || selectedItems.value.length),
)

function toggleFilterItem(key: string) {
  const index = selectedItems.value.indexOf(key)
  if (index === -1) selectedItems.value = [...selectedItems.value, key]
  else selectedItems.value = selectedItems.value.filter((item) => item !== key)
}

function clearFilters() {
  filterId.value = ''
  filterRace.value = null
  selectedItems.value = []
}

watch(filterRace, (race) => {
  if (!race) return
  selectedItems.value = selectedItems.value.filter((key) => catalog[key]?.race === race)
})

function handleOutsideClick(event: MouseEvent) {
  if (!filtersOpen.value) return
  if (pickerRef.value?.contains(event.target as Node)) return
  filtersOpen.value = false
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') filtersOpen.value = false
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
  document.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick)
  document.removeEventListener('keydown', handleKeydown)
})

function playerHasItem(player: FolderReplayPlayer, key: string): boolean {
  const item = catalog[key]
  if (!item) return false
  if (item.kind === 'unit') {
    return player.units.some((unit) => resolveItem(unit.unit)?.key === key)
  }
  if (item.kind === 'upgrade') {
    return (['early', 'mid', 'late'] as const).some((phase) =>
      player.tech[phase].some((tech) => resolveItem(tech.tech)?.key === key),
    )
  }
  return (player.buildings || []).some((building) => resolveItem(building.building)?.key === key)
}

const filteredReplays = computed(() => {
  const idQuery = filterId.value.trim().toLowerCase()
  const race = filterRace.value
  const itemKeys = selectedItems.value
  if (!idQuery && !race && itemKeys.length === 0) return props.replays

  return props.replays.filter((replay) => {
    const gameIdMatch = Boolean(idQuery && String(replay.game_id).includes(idQuery))
    return replay.player_details.some((player) => {
      if (race && raceFromName(player.race) !== race) return false
      if (itemKeys.length > 0 && !itemKeys.some((key) => playerHasItem(player, key))) {
        return false
      }
      if (idQuery && !gameIdMatch && !player.name.toLowerCase().includes(idQuery)) return false
      return true
    })
  })
})

const phases = [
  { key: 'early' as const, short: '前' },
  { key: 'mid' as const, short: '中' },
  { key: 'late' as const, short: '后' },
]

function raceLetter(race: string | null): string {
  return raceFromName(race) || '?'
}

function raceClass(race: string | null): string {
  return (raceFromName(race) || '').toLowerCase()
}

function unitPreview(player: FolderReplayPlayer) {
  const grouped = new Map<string, { key: string; count: number; name: string; icon: string }>()
  for (const unit of player.units) {
    const item = resolveItem(unit.unit)
    if (!item || item.kind !== 'unit') continue
    if (AUTO_SPAWNED_UNITS.has(item.key) || AUTO_SPAWNED_UNITS.has(unit.unit)) continue
    if (!settings.showLibraryWorkers && WORKER_UNITS.has(item.key)) continue
    const current = grouped.get(item.key)
    if (current) {
      current.count += unit.count
      continue
    }
    grouped.set(item.key, {
      key: item.key,
      count: unit.count,
      name: displayName(item, unit.unit),
      icon: iconUrl(item.abbr),
    })
  }
  return [...grouped.values()]
}

function phaseTech(player: FolderReplayPlayer, phase: 'early' | 'mid' | 'late') {
  return player.tech[phase].filter((tech) => resolveItem(tech.tech))
}

function techIcon(tech: string): string {
  const item = resolveItem(tech)
  return item ? itemIconUrl(item) : ''
}

function techName(tech: string): string {
  return displayName(resolveItem(tech), tech)
}
</script>

<style scoped>
.library {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 18px 22px 24px;
  scrollbar-width: thin;
  scrollbar-color: #31527a transparent;
}

.library-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.eyebrow {
  color: #5f7d9f;
  font-size: 10px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.library-head h2 {
  margin: 2px 0 0;
  color: #dcecff;
  font-size: 22px;
  font-weight: 700;
}

.library-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  color: #6f89ad;
  font-size: 11px;
}

.library-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 10px;
  border: 1px solid #162a45;
  border-radius: 8px;
  background: rgba(8, 16, 28, 0.72);
}

.filter-id {
  width: 180px;
  height: 28px;
  padding: 0 8px;
  border: 1px solid #1d3352;
  border-radius: 6px;
  background: #070d18;
  color: #b8d0ea;
  font-size: 11px;
  outline: none;
}

.filter-id::placeholder {
  color: #4f6b8c;
}

.filter-id:focus {
  border-color: #2f6caf;
}

.filter-picker {
  position: relative;
}

.filter-picker-button {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 9px;
  border: 1px solid #1d3352;
  border-radius: 6px;
  background: #070d18;
  color: #8fb0d4;
  font-size: 11px;
  cursor: pointer;
}

.filter-picker-button:hover,
.filter-picker-button.active {
  border-color: #3d7fc4;
  color: #d8ebff;
}

.filter-count-badge {
  display: grid;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  place-items: center;
  border-radius: 999px;
  background: #245a94;
  color: #eaf4ff;
  font-size: 9px;
  font-weight: 700;
}

.filter-caret {
  color: #5f7d9f;
  font-size: 9px;
}

.filter-panel {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 30;
  width: min(760px, calc(100vw - 380px));
  min-width: 560px;
  border: 1px solid #24466f;
  border-radius: 10px;
  background: #08111f;
  box-shadow: 0 18px 46px rgba(0, 0, 0, 0.6);
}

.filter-columns {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  max-height: 330px;
  padding: 12px;
  overflow: auto;
  scrollbar-width: thin;
  scrollbar-color: #31527a transparent;
}

.filter-column {
  min-width: 0;
}

.filter-column-title {
  margin-bottom: 6px;
  color: #7ca5cf;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.filter-option-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.filter-option {
  position: relative;
  width: 30px;
  height: 30px;
  padding: 0;
  border: 1px solid #1d3352;
  border-radius: 5px;
  background: #0b1424;
  cursor: pointer;
  opacity: 0.62;
  transition: opacity 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
}

.filter-option:hover {
  opacity: 1;
  border-color: #2f6caf;
}

.filter-option.selected {
  opacity: 1;
  border-color: #58a6ff;
  box-shadow: 0 0 8px rgba(88, 166, 255, 0.5);
}

.filter-option.selected::after {
  content: '';
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 7px;
  height: 7px;
  border: 1px solid #08111f;
  border-radius: 50%;
  background: #58a6ff;
}

.filter-option img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

.filter-panel-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid #162a45;
}

.filter-hint {
  margin-right: auto;
  color: #4f6b8c;
  font-size: 10px;
}

.filter-panel-clear,
.filter-panel-done {
  height: 26px;
  padding: 0 9px;
  border: 1px solid #1d3352;
  border-radius: 5px;
  background: transparent;
  color: #8fb0d4;
  font-size: 10px;
  cursor: pointer;
}

.filter-panel-done {
  border-color: #3d7fc4;
  background: #173a61;
  color: #eaf4ff;
}

.filter-selected {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.filter-selected-chip {
  position: relative;
  width: 26px;
  height: 26px;
  padding: 0;
  border: 1px solid #3d7fc4;
  border-radius: 5px;
  background: #0b1424;
  cursor: pointer;
}

.filter-selected-chip img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

.selected-remove {
  position: absolute;
  top: -5px;
  right: -5px;
  display: grid;
  width: 12px;
  height: 12px;
  place-items: center;
  border-radius: 50%;
  background: #243c5e;
  color: #dbe9fb;
  font-size: 9px;
  line-height: 1;
}

.filter-races {
  display: flex;
  border: 1px solid #1d3352;
  border-radius: 6px;
  overflow: hidden;
}

.filter-races button {
  height: 28px;
  padding: 0 8px;
  border: 0;
  background: transparent;
  color: #6f89ad;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
}

.filter-races button + button {
  border-left: 1px solid #1d3352;
}

.filter-races button.active {
  background: #173a61;
  color: #d9ecff;
}

.filter-races button.p.active {
  background: rgba(105, 219, 124, 0.18);
  color: #69db7c;
}

.filter-races button.t.active {
  background: rgba(116, 192, 252, 0.18);
  color: #74c0fc;
}

.filter-races button.z.active {
  background: rgba(177, 151, 252, 0.18);
  color: #b197fc;
}

.filter-clear {
  height: 28px;
  padding: 0 9px;
  border: 1px solid #1d3352;
  border-radius: 6px;
  background: transparent;
  color: #7f9ab9;
  font-size: 10px;
  cursor: pointer;
}

.filter-clear:hover {
  border-color: #3d7fc4;
  color: #e8f4ff;
}

.phase-legend {
  display: flex;
  align-items: center;
  gap: 4px;
}

.phase-dot {
  width: 7px;
  height: 7px;
  border-radius: 2px;
  margin-left: 5px;
}

.phase-dot.early {
  background: #69db7c;
}

.phase-dot.mid {
  background: #d29922;
}

.phase-dot.late {
  background: #b197fc;
}

.replay-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.replay-card {
  display: grid;
  grid-template-columns: 190px minmax(0, 1fr) minmax(0, 1fr);
  gap: 14px;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #16263d;
  border-radius: 9px;
  background: rgba(8, 15, 28, 0.75);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color 140ms ease, background 140ms ease;
}

.replay-card:hover {
  border-color: #2f6caf;
  background: rgba(14, 29, 48, 0.9);
}

.replay-map {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding-right: 10px;
  border-right: 1px solid #142238;
}

.map-name {
  color: #dcecff;
  font-size: 14px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.map-meta {
  display: flex;
  gap: 10px;
  color: #6f89ad;
  font-size: 11px;
}

.winner {
  color: #d9b45b;
}

.map-file {
  color: #425d7c;
  font-size: 9px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.player-summary {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.player-head {
  display: flex;
  align-items: center;
  gap: 6px;
}

.race-badge {
  width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
  border-radius: 4px;
  background: #1a2b44;
  color: #9fb8d8;
  font-size: 10px;
  font-weight: 700;
}

.race-badge.p {
  background: rgba(105, 219, 124, 0.22);
  color: #69db7c;
}

.race-badge.t {
  background: rgba(116, 192, 252, 0.22);
  color: #74c0fc;
}

.race-badge.z {
  background: rgba(177, 151, 252, 0.22);
  color: #b197fc;
}

.player-name {
  color: #dcecff;
  font-size: 13px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.player-result {
  margin-left: auto;
  color: #5f7d9f;
  font-size: 10px;
}

.player-result.win {
  color: #d9b45b;
}

.summary-line {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  min-width: 0;
}

.summary-label {
  flex: none;
  width: 26px;
  padding-top: 3px;
  color: #4f6b8c;
  font-size: 10px;
}

.chip-row,
.tech-icons {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  min-width: 0;
}

.unit-chip,
.tech-chip {
  position: relative;
  display: inline-flex;
  align-items: center;
  border: 1px solid #1d3352;
  border-radius: 5px;
  background: #0b1424;
}

.unit-chip {
  width: 38px;
  height: 38px;
  padding: 0;
  border-color: #2c5480;
  background: #0b1424;
}

.unit-chip img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

.chip-count {
  position: absolute;
  right: 2px;
  bottom: 2px;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  text-shadow:
    0 0 2px #000,
    0 0 4px #000,
    0 1px 2px #000;
}

.tech-groups {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  min-width: 0;
}

.tech-phase {
  display: flex;
  align-items: flex-start;
  gap: 4px;
}

.phase-label {
  padding-top: 3px;
  font-size: 9px;
  font-weight: 700;
}

.phase-label.early {
  color: #69db7c;
}

.phase-label.mid {
  color: #d29922;
}

.phase-label.late {
  color: #b197fc;
}

.tech-chip {
  padding: 1px;
}

.tech-chip img {
  width: 24px;
  height: 24px;
  object-fit: contain;
  border-radius: 3px;
}

.none {
  color: #3d5575;
  font-size: 10px;
  padding-top: 3px;
}

.library-empty {
  padding: 40px;
  text-align: center;
  color: #5f7d9f;
  font-size: 13px;
  border: 1px dashed #1d3352;
  border-radius: 10px;
}

@media (max-width: 1100px) {
  .replay-card {
    grid-template-columns: 155px minmax(0, 1fr) minmax(0, 1fr);
    gap: 9px;
  }

  .replay-card .player-summary {
    font-size: 11px;
  }
}
</style>
