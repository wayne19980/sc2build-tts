<template>
  <div class="build-orders">
    <div
      v-for="(player, idx) in allPlayers"
      :key="idx"
      class="player-panel"
    >
      <div class="player-header" :class="player.teamClass">
        <span class="race-badge" :class="player.race">{{ player.race }}</span>
        <span class="player-name">{{ player.name || 'Unknown' }}</span>
        <button
          type="button"
          class="voice-reader-btn"
          @click="$emit('open-voice', player.playerData)"
        >
          <span>🔊</span>语音播报
        </button>
        <button type="button" class="export-btn" @click="exportTxt(idx)">
          导出TXT
        </button>
      </div>
      <div class="build-list" :ref="(el) => setBuildListRef(idx, el)">
        <div
          v-for="(item, j) in player.items"
          :key="j"
          class="build-item"
          :class="item.extraClass"
        >
          <span class="time">{{ item.timeStr }}</span>
          <span class="supply">{{ item.supplyStr }}</span>
          <span class="unit">{{ item.unitText }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type { ReplayData, PlayerData, ProcessedBuildItem } from '../types'
import { formatGameTime } from '../utils'
import { getDisplayUnitText } from '../composables/useTranslation'

const props = defineProps<{
  data: ReplayData
  showOriginal: boolean
  showWorkers: boolean
  mergeSameActions: boolean
}>()

defineEmits<{
  (e: 'open-voice', player: PlayerData): void
}>()

interface FlatPlayer {
  name: string
  race: string
  teamClass: string
  items: ProcessedBuildItem[]
  playerData: PlayerData
}

const buildListRefs = ref<Record<number, HTMLElement>>({})
function setBuildListRef(idx: number, el: any) {
  if (el) buildListRefs.value[idx] = el as HTMLElement
}

const allPlayers = computed<FlatPlayer[]>(() => {
  const result: FlatPlayer[] = []
  const teamClasses = ['team1', 'team2']
  props.data.teams.forEach((team, i) => {
    team.players.forEach((player) => {
      const race = (player.race || '?')[0].toUpperCase()
      let items = [...(player.build_order || [])]

      if (!props.showWorkers) {
        items = items.filter((it) => !it.is_worker)
      }

      let processed: ProcessedBuildItem[] = items.map((it) => ({
        timeStr: formatGameTime(it.start_time),
        supplyStr: String(it.supply ?? ''),
        unitText: getDisplayUnitText(it, props.showOriginal),
        extraClass: it.is_worker
          ? 'unit'
          : it._kind === 'upgrade'
            ? 'upgrade'
            : '',
        raw: it,
      }))

      if (props.mergeSameActions) {
        const merged: ProcessedBuildItem[] = []
        let current: ProcessedBuildItem | null = null
        let count = 0
        const flush = () => {
          if (!current) return
          merged.push({
            ...current,
            unitText:
              count > 1 ? `${current.unitText} x${count}` : current.unitText,
          })
        }
        processed.forEach((item) => {
          if (
            !current ||
            current.timeStr !== item.timeStr ||
            current.unitText !== item.unitText
          ) {
            flush()
            current = item
            count = 1
          } else {
            count++
            current = { ...current, supplyStr: item.supplyStr }
          }
        })
        flush()
        processed = merged
      }

      result.push({
        name: player.name,
        race,
        teamClass: teamClasses[i] || '',
        items: processed,
        playerData: player,
      })
    })
  })
  return result
})

function exportTxt(playerIdx: number) {
  const player = allPlayers.value[playerIdx]
  if (!player) return
  const lines = player.items.map((it) => {
    const parts: string[] = []
    if (it.timeStr) parts.push(it.timeStr)
    if (it.supplyStr) parts.push(it.supplyStr)
    if (it.unitText) parts.push(it.unitText)
    return parts.join(' ')
  })
  const content = lines.join('\n')
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${player.name || 'player'}_build.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.build-orders {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 768px) {
  .build-orders {
    grid-template-columns: 1fr;
  }
}

.player-panel {
  background: var(--bg-card);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
}

.player-header {
  padding: 1rem 1.25rem;
  font-weight: 600;
  font-size: 1rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.player-header.team1 {
  background: linear-gradient(90deg, rgba(116, 192, 252, 0.15), transparent);
}

.player-header.team2 {
  background: linear-gradient(90deg, rgba(249, 81, 73, 0.15), transparent);
}

.race-badge {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 0.85rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.race-badge.T {
  background: rgba(116, 192, 252, 0.3);
  color: var(--race-t);
}

.race-badge.P {
  background: rgba(177, 151, 252, 0.3);
  color: var(--race-p);
}

.race-badge.Z {
  background: rgba(105, 219, 124, 0.3);
  color: var(--race-z);
}

.player-name {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.voice-reader-btn {
  background: rgba(168, 85, 247, 0.1);
  color: var(--purple);
  border: 1px solid rgba(168, 85, 247, 0.2);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 0.75rem;
  cursor: pointer;
  margin-right: 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.2s;
}

.voice-reader-btn:hover {
  background: rgba(168, 85, 247, 0.2);
  border-color: var(--purple);
}

.voice-reader-btn span {
  font-size: 0.9rem;
}

.export-btn {
  margin-left: auto;
  padding: 0.2rem 0.75rem;
  font-size: 0.8rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: rgba(88, 166, 255, 0.08);
  color: var(--accent-blue);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.export-btn::before {
  content: '⇩';
  font-size: 0.9em;
}

.export-btn:hover {
  border-color: var(--accent-blue);
  background: rgba(88, 166, 255, 0.2);
}

.build-list {
  max-height: 400px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--accent-blue) transparent;
}

.build-list::-webkit-scrollbar {
  width: 8px;
}

.build-list::-webkit-scrollbar-track {
  background: transparent;
}

.build-list::-webkit-scrollbar-thumb {
  background: rgba(88, 166, 255, 0.4);
  border-radius: 999px;
  border: 2px solid transparent;
  background-clip: padding-box;
}

.build-list::-webkit-scrollbar-thumb:hover {
  background: rgba(88, 166, 255, 0.8);
}

.build-item {
  display: grid;
  grid-template-columns: 60px 50px 1fr;
  gap: 0.75rem;
  padding: 0.5rem 1.25rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  border-bottom: 1px solid var(--border);
  align-items: center;
}

.build-item:last-child {
  border-bottom: none;
}

.build-item:hover {
  background: var(--bg-hover);
}

.build-item .time {
  color: var(--text-muted);
  font-weight: 500;
}

.build-item .supply {
  color: var(--accent-orange);
  font-size: 0.8rem;
}

.build-item .unit {
  color: var(--text);
}

.build-item.upgrade .unit,
.build-item.upgrade .time {
  color: var(--accent-red);
}

.build-item.unit .unit {
  color: var(--accent-orange);
}
</style>
