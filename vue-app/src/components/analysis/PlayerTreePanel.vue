<template>
  <section class="player-tree-panel">
    <header class="panel-top">
      <div class="player-copy">
        <span class="race-dot" :class="raceClass" />
        <span class="name">{{ player.name }}</span>
        <span class="race">{{ raceLabel }}</span>
        <span v-if="player.is_winner" class="winner">★</span>
        <SupplyBreakdown :supply="supply" />
      </div>
      <div class="panel-actions">
        <button
          class="view-mode-toggle"
          :class="{ active: viewMode === 'flow' }"
          :title="viewMode === 'flow' ? '切换为全景连线画布' : '切换为自适应分层流'"
          @click="viewMode = viewMode === 'flow' ? 'canvas' : 'flow'"
        >
          {{ viewMode === 'flow' ? '自适应' : '全景' }}
        </button>
      </div>
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
      :orders="orders"
      :production="production"
      :speed="speed"
      :view-mode="viewMode"
      compact
    />
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import type {
  EventItem,
  PlayerInfo,
  ProductionTaskView,
  SupplyInfo,
  TechTiming,
  UnitLifecycle,
} from '../../types-analysis'
import { raceFromName } from '../../data/catalog'
import ScaledTree from './ScaledTree.vue'
import SupplyBreakdown from './SupplyBreakdown.vue'

const viewMode = ref<'canvas' | 'flow'>('flow')

const props = defineProps<{
  player: PlayerInfo
  time: number
  countMode: 'cumulative' | 'alive'
  buildings: EventItem[]
  units: UnitLifecycle[]
  tech: TechTiming[]
  orders?: EventItem[]
  production?: ProductionTaskView[]
  speed: number
  supply?: SupplyInfo
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
  background: #69db7c;
  box-shadow: 0 0 6px rgba(105, 219, 124, 0.7);
}

.race-dot.t {
  background: #74c0fc;
  box-shadow: 0 0 6px rgba(116, 192, 252, 0.7);
}

.race-dot.z {
  background: #b197fc;
  box-shadow: 0 0 6px rgba(177, 151, 252, 0.7);
}

.winner {
  color: #e5bd5f;
  font-size: 12px;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.view-mode-toggle {
  padding: 2px 7px;
  border-radius: 4px;
  border: 1px solid #1c3250;
  background: rgba(12, 23, 40, 0.7);
  color: #7ca5cf;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.view-mode-toggle:hover {
  background: rgba(25, 45, 75, 0.85);
  color: #d8eaff;
  border-color: #2b5080;
}

.view-mode-toggle.active {
  background: rgba(45, 100, 180, 0.25);
  border-color: rgba(75, 155, 240, 0.6);
  color: #a5d2ff;
}
</style>
