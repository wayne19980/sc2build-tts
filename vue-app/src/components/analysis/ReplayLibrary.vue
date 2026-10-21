<template>
  <div class="library">
    <header class="library-head">
      <div>
        <div class="eyebrow">Replay Library</div>
        <h2>{{ folderName || '对局列表' }}</h2>
      </div>
      <div class="library-meta">
        <span>{{ replays.length }} 场</span>
        <span class="phase-legend">
          <i class="phase-dot early" />前
          <i class="phase-dot mid" />中
          <i class="phase-dot late" />后
        </span>
      </div>
    </header>

    <div v-if="loading" class="library-empty">正在读取对局…</div>
    <div v-else-if="replays.length === 0" class="library-empty">
      这个文件夹还没有导入录像
    </div>

    <div v-else class="replay-list">
      <button
        v-for="replay in replays"
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
import type { FolderReplay, FolderReplayPlayer } from '../../types-analysis'
import { AUTO_SPAWNED_UNITS, formatClock, iconUrl, itemIconUrl, raceFromName, resolveItem } from '../../data/catalog'
import { upgradeFamily } from '../../data/upgrades'
import { useLanguage } from '../../composables/useLanguage'

defineProps<{
  replays: FolderReplay[]
  folderName: string
  loading: boolean
}>()

defineEmits<{
  (event: 'open', replay: FolderReplay): void
}>()

const { displayName } = useLanguage()

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

interface TechEntry {
  tech: string
  t_sec: number
  phase: 'early' | 'mid' | 'late'
}

function collapsedTech(player: FolderReplayPlayer): TechEntry[] {
  const singles: TechEntry[] = []
  const families = new Map<string, { entry: TechEntry; index: number }>()

  for (const phase of phases) {
    for (const tech of player.tech[phase.key]) {
      const item = resolveItem(tech.tech)
      if (!item) continue
      const entry: TechEntry = { tech: tech.tech, t_sec: tech.t_sec, phase: phase.key }
      const family = upgradeFamily(item.key)
      if (!family) {
        singles.push(entry)
        continue
      }
      const index = family.indexOf(item.key)
      const current = families.get(family[0])
      if (
        !current ||
        index > current.index ||
        (index === current.index && tech.t_sec < current.entry.t_sec)
      ) {
        families.set(family[0], { entry, index })
      }
    }
  }

  return [...singles, ...[...families.values()].map((value) => value.entry)].sort(
    (a, b) => a.t_sec - b.t_sec,
  )
}

function phaseTech(player: FolderReplayPlayer, phase: 'early' | 'mid' | 'late') {
  return collapsedTech(player).filter((tech) => tech.phase === phase)
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
  background: rgba(177, 151, 252, 0.22);
  color: #b197fc;
}

.race-badge.t {
  background: rgba(116, 192, 252, 0.22);
  color: #74c0fc;
}

.race-badge.z {
  background: rgba(105, 219, 124, 0.22);
  color: #69db7c;
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
