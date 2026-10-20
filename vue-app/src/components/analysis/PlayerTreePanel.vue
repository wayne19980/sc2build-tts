<template>
  <section class="player-tree-panel">
    <header class="panel-top">
      <div class="player-copy">
        <span class="race-dot" :class="raceClass" />
        <span class="name">{{ player.name }}</span>
        <span class="race">{{ raceLabel }}</span>
      </div>
      <span v-if="player.is_winner" class="winner">★</span>
    </header>
    <ScaledTree
      v-if="race"
      :race="race"
      :player-id="player.id"
      :time="time"
      :count-mode="countMode"
      :buildings="playerBuildings"
      :units="playerUnits"
      :tech="playerTech"
      :speed="speed"
      compact
    />
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EventItem, PlayerInfo, TechTiming, UnitLifecycle } from '../../types-analysis'
import { raceFromName } from '../../data/catalog'
import ScaledTree from './ScaledTree.vue'

const props = defineProps<{
  player: PlayerInfo
  time: number
  countMode: 'cumulative' | 'alive'
  buildings: EventItem[]
  units: UnitLifecycle[]
  tech: TechTiming[]
  speed: number
}>()

const race = computed(() => raceFromName(props.player.race))
const raceClass = computed(() => race.value?.toLowerCase() || '')
const raceLabel = computed(() => (race.value === 'P' ? 'Protoss' : race.value === 'T' ? 'Terran' : race.value === 'Z' ? 'Zerg' : '?'))
const playerBuildings = computed(() => props.buildings.filter((event) => event.player_id === props.player.id))
const playerUnits = computed(() => props.units.filter((unit) => unit.player_id === props.player.id))
const playerTech = computed(() => props.tech.filter((timing) => timing.player_id === props.player.id))
</script>

<style scoped>
.player-tree-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border: 0;
  border-right: 1px solid #142238;
  background: rgba(7, 13, 24, 0.3);
}

.player-tree-panel:last-child {
  border-right: 0;
}

.player-tree-panel :deep(.scaled-tree) {
  align-items: flex-start;
  padding-top: 8px;
}

.panel-top {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 5px 10px;
  border-bottom: 1px solid #142238;
  background: rgba(8, 16, 29, 0.75);
}

.player-copy {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.name {
  color: #dcecff;
  font-size: 12px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.race {
  color: #6f89ad;
  font-size: 10px;
}

.race-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6f89ad;
}

.race-dot.p {
  background: #b197fc;
  box-shadow: 0 0 6px rgba(177, 151, 252, 0.7);
}

.race-dot.t {
  background: #74c0fc;
  box-shadow: 0 0 6px rgba(116, 192, 252, 0.7);
}

.race-dot.z {
  background: #69db7c;
  box-shadow: 0 0 6px rgba(105, 219, 124, 0.7);
}

.winner {
  color: #e5bd5f;
  font-size: 12px;
}
</style>
