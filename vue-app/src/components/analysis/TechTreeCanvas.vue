<template>
  <div class="tree-scroll">
    <div class="tree-canvas" :style="{ width: `${canvasWidth}px`, height: `${canvasHeight}px` }">
      <svg class="edges" :width="canvasWidth" :height="canvasHeight">
        <defs>
          <linearGradient id="edgeGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#213a5c" />
            <stop offset="55%" stop-color="#3c76b5" />
            <stop offset="100%" stop-color="#58a6ff" />
          </linearGradient>
          <filter id="edgeGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow
              dx="0"
              dy="0"
              stdDeviation="2.2"
              flood-color="#3d7fc4"
              flood-opacity="0.55"
            />
          </filter>
        </defs>
        <path
          v-for="edge in edges"
          :key="edge.id"
          :d="edge.path"
          fill="none"
          stroke="url(#edgeGradient)"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          opacity="0.58"
          filter="url(#edgeGlow)"
        />
      </svg>

      <div
        v-for="node in buildingNodes"
        :key="node.key"
        class="building-node"
        :class="node.state"
        :style="{ left: `${node.left}px`, top: `${node.top}px` }"
      >
        <div class="building-main">
          <div class="icon-shell building-icon" :class="{ 'unlock-flash': node.flash }" :title="tooltip(node.item)">
            <img :src="iconUrl(node.item.abbr)" :alt="node.item.name" draggable="false" />
            <span v-if="node.count > 0" class="count-badge building-badge">{{ node.count }}</span>
            <div
              v-if="node.constructing > 0"
              class="build-progress"
              :class="{ indeterminate: node.indeterminate }"
            >
              <div class="build-progress-fill" :style="{ width: `${node.progress * 100}%` }" />
            </div>
            <div v-if="node.morphs.length" class="morph-badges">
              <span
                v-for="morph in node.morphs"
                :key="morph.key"
                class="morph-badge"
                :title="`${morph.item.nameZh} ×${morph.count}`"
              >
                <img :src="iconUrl(morph.item.abbr)" :alt="morph.item.name" draggable="false" />
                <span class="morph-count">{{ morph.count }}</span>
              </span>
            </div>
          </div>
          <div v-if="node.units.length" class="unit-grid">
            <div
              v-for="unit in node.units"
              :key="unit.key"
              class="icon-shell unit-icon"
              :class="{ locked: !unit.unlocked, empty: unit.count === 0, 'unlock-flash': unit.flash }"
              :title="tooltip(unit.item, unit.count)"
            >
              <img :src="iconUrl(unit.item.abbr)" :alt="unit.item.name" draggable="false" />
              <span v-if="unit.count > 0" class="count-badge">{{ unit.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="otherNode"
        class="other-node"
        :style="{ left: `${otherNode.left}px`, top: `${otherNode.top}px` }"
      >
        <div class="other-label">其他单位</div>
        <div class="unit-grid other-grid">
          <div
            v-for="unit in otherNode.units"
            :key="unit.key"
            class="icon-shell unit-icon"
            :class="{ locked: !unit.unlocked, empty: unit.count === 0, 'unlock-flash': unit.flash }"
            :title="tooltip(unit.item, unit.count)"
          >
            <img :src="iconUrl(unit.item.abbr)" :alt="unit.item.name" draggable="false" />
            <span v-if="unit.count > 0" class="count-badge">{{ unit.count }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EventItem, Race, TechTiming, UnitLifecycle } from '../../types-analysis'
import { iconUrl, resolveItem, techTrees, type CatalogItem } from '../../data/catalog'
import { CELL_W, CELL_W_COMPACT, MARGIN, ROW_H } from '../../data/layout'
import { useLanguage } from '../../composables/useLanguage'

const props = defineProps<{
  race: Race
  playerId: number
  time: number
  countMode: 'cumulative' | 'alive'
  buildings: EventItem[]
  units: UnitLifecycle[]
  tech: TechTiming[]
  compact?: boolean
}>()


interface BuildingCounter {
  done: number
  constructing: number
  ever: boolean
  morphs: Record<string, number>
  firstDoneT?: number
}

interface BuildingNode {
  key: string
  left: number
  top: number
  item: CatalogItem
  state: 'locked' | 'building' | 'done' | 'destroyed'
  count: number
  units: UnitNode[]
  morphs: { key: string; item: CatalogItem; count: number }[]
  flash: boolean
  constructing: number
  progress: number
  indeterminate: boolean
}

interface UnitNode {
  key: string
  item: CatalogItem
  count: number
  unlocked: boolean
  flash: boolean
}

const { displayName } = useLanguage()
const tree = computed(() => techTrees[props.race])
const cellWidth = computed(() => (props.compact ? CELL_W_COMPACT : CELL_W))

const buildingStats = computed(() => {
  const counters: Record<string, BuildingCounter> = {}
  const live = new Map<number, { name: string; status: 'building' | 'done' }>()

  const counter = (key: string) => {
    if (!counters[key]) {
      counters[key] = { done: 0, constructing: 0, ever: false, morphs: {} }
    }
    return counters[key]
  }
  const addConstructing = (key: string) => {
    counter(key).constructing += 1
  }
  const removeConstructing = (key: string) => {
    counter(key).constructing = Math.max(0, counter(key).constructing - 1)
  }
  const addDone = (key: string, at: number) => {
    const target = counter(key)
    target.done += 1
    target.ever = true
    if (target.firstDoneT === undefined) target.firstDoneT = at
  }
  const removeDone = (key: string) => {
    counter(key).done = Math.max(0, counter(key).done - 1)
  }

  for (const event of props.buildings) {
    if (event.player_id !== props.playerId || event.t_sec > props.time) continue
    const item = resolveItem(event.name)
    if (!item || item.kind !== 'building') continue
    const unitId = Number(event.payload?.unit_id)
    const hasUnitId = Number.isFinite(unitId)
    const previous = hasUnitId ? live.get(unitId) : undefined

    if (event.kind === 'build_start') {
      if (previous?.status === 'building') continue
      if (previous?.status === 'done') continue
      if (hasUnitId) live.set(unitId, { name: item.key, status: 'building' })
      addConstructing(item.key)
    } else if (event.kind === 'build_done' || event.kind === 'unit_born') {
      if (previous?.status === 'done') continue
      if (previous?.status === 'building') removeConstructing(previous.name)
      if (hasUnitId) live.set(unitId, { name: item.key, status: 'done' })
      addDone(item.key, event.t_sec)
    } else if (event.kind === 'unit_morph') {
      if (previous?.status === 'done' && previous.name === item.key) continue
      if (previous?.status === 'building') removeConstructing(previous.name)
      if (previous && previous.name !== item.key) {
        const base = counter(previous.name)
        base.morphs[item.key] = (base.morphs[item.key] || 0) + 1
      }
      if (hasUnitId) live.set(unitId, { name: item.key, status: 'done' })
      addDone(item.key, event.t_sec)
    } else if (event.kind === 'unit_died') {
      if (previous?.status === 'done') removeDone(previous.name)
      if (hasUnitId) live.delete(unitId)
    }
  }

  return counters
})

const unitCounts = computed(() => {
  const counts: Record<string, number> = {}
  const add = (key: string) => {
    counts[key] = (counts[key] || 0) + 1
  }

  for (const unit of props.units) {
    if (unit.player_id !== props.playerId) continue
    if (unit.born_t_sec > props.time) continue

    if (props.countMode === 'alive') {
      if (unit.died_t_sec === null || unit.died_t_sec > props.time) {
        add(unit.unit_type)
      }
      continue
    }

    add(unit.first_type)
    for (const morph of unit.morphs) {
      if (morph.t_sec <= props.time) add(morph.to)
    }
  }
  return counts
})

const unitItems = computed(() => {
  const grouped = new Map<string, UnitNode[]>()
  const time = props.time
  for (const group of tree.value.unitGroups) {
    const units: UnitNode[] = []
    for (const unit of group.units) {
      const item = resolveItem(unit.key)
      if (!item) continue
      const requirements = unit.requiresAny.length ? unit.requiresAny : [group.group]
      const unlockTimes = requirements
        .map((requirement) => buildingStats.value[requirement]?.firstDoneT)
        .filter((value): value is number => value !== undefined)
      const unlockAt = unlockTimes.length ? Math.min(...unlockTimes) : undefined
      const unlocked = unlockAt !== undefined
      units.push({
        key: item.key,
        item,
        count: unitCounts.value[item.key] || 0,
        unlocked,
        flash: unlocked && time >= unlockAt && time - unlockAt < 1.2,
      })
    }
    grouped.set(group.group, units)
  }
  return grouped
})

const constructionProgress = computed(() => {
  const tasks = new Map<number, { name: string; start: number; done?: number }>()
  for (const event of props.buildings) {
    if (event.player_id !== props.playerId) continue
    const unitId = Number(event.payload?.unit_id)
    if (!Number.isFinite(unitId)) continue
    if (event.kind === 'build_start') {
      tasks.set(unitId, { name: event.name, start: event.t_sec })
    } else if (event.kind === 'build_done' || event.kind === 'unit_born') {
      const task = tasks.get(unitId)
      if (task && task.done === undefined) task.done = event.t_sec
    }
  }

  const result: Record<
    string,
    { count: number; progress: number; indeterminate: boolean }
  > = {}
  for (const task of tasks.values()) {
    if (task.start > props.time) continue
    if (task.done !== undefined && task.done <= props.time) continue
    const item = resolveItem(task.name)
    if (!item || item.kind !== 'building') continue
    const entry = result[item.key] || { count: 0, progress: 0, indeterminate: false }
    const progress =
      task.done !== undefined && task.done > task.start
        ? Math.min(1, Math.max(0, (props.time - task.start) / (task.done - task.start)))
        : 0
    entry.count += 1
    entry.progress += progress
    if (task.done === undefined) entry.indeterminate = true
    result[item.key] = entry
  }
  for (const entry of Object.values(result)) {
    if (entry.count) entry.progress /= entry.count
  }
  return result
})

const buildingNodes = computed<BuildingNode[]>(() => {
  const treeKeys = new Set(tree.value.buildings.map((building) => building.key))
  return tree.value.buildings.map((building) => {
    const stats = buildingStats.value[building.key]
    let state: BuildingNode['state'] = 'locked'
    if (stats?.done) state = 'done'
    else if (stats?.constructing) state = 'building'
    else if (stats?.ever) state = 'destroyed'

    return {
      key: building.key,
      left: MARGIN + building.x * cellWidth.value,
      top: MARGIN + building.y * ROW_H,
      item: resolveItem(building.key)!,
      state,
      count: stats?.done || 0,
      constructing: constructionProgress.value[building.key]?.count || 0,
      progress: constructionProgress.value[building.key]?.progress || 0,
      indeterminate: constructionProgress.value[building.key]?.indeterminate || false,
      flash:
        stats?.firstDoneT !== undefined &&
        props.time >= stats.firstDoneT &&
        props.time - stats.firstDoneT < 1.2,
      units: unitItems.value.get(building.key) || [],
      morphs: Object.entries(stats?.morphs || {})
        .map(([key, count]) => {
          const item = resolveItem(key)
          return item && item.kind === 'building' && !treeKeys.has(key)
            ? { key, item, count }
            : null
        })
        .filter((entry): entry is { key: string; item: CatalogItem; count: number } => entry !== null),
    }
  })
})

const otherNode = computed(() => {
  if (!tree.value.otherUnits.length) return null
  const maxX = Math.max(...tree.value.buildings.map((building) => building.x))
  const maxY = Math.max(...tree.value.buildings.map((building) => building.y))
  const units: UnitNode[] = tree.value.otherUnits
    .map((unit) => {
      const item = resolveItem(unit.key)
      if (!item) return null
      const unlockTimes = unit.requiresAny
        .map((requirement) => buildingStats.value[requirement]?.firstDoneT)
        .filter((value): value is number => value !== undefined)
      const unlockAt = unlockTimes.length ? Math.min(...unlockTimes) : undefined
      return {
        key: item.key,
        item,
        count: unitCounts.value[item.key] || 0,
        unlocked: unlockAt !== undefined,
        flash: unlockAt !== undefined && props.time >= unlockAt && props.time - unlockAt < 1.2,
      }
    })
    .filter((unit): unit is UnitNode => unit !== null)

  return {
    left: MARGIN + maxX * cellWidth.value,
    top: MARGIN + (maxY + 1) * ROW_H,
    units,
  }
})

const maxX = computed(() => Math.max(...tree.value.buildings.map((building) => building.x)))
const maxY = computed(() => Math.max(...tree.value.buildings.map((building) => building.y)))
const canvasWidth = computed(() => (maxX.value + 1) * cellWidth.value + MARGIN * 2)
const canvasHeight = computed(
  () => (maxY.value + (otherNode.value ? 2 : 1)) * ROW_H + MARGIN * 2,
)

interface Edge {
  id: string
  path: string
}

const edges = computed<Edge[]>(() => {
  const positions = new Map<string, { left: number; top: number }>()
  for (const node of buildingNodes.value) {
    positions.set(node.key, { left: node.left, top: node.top })
  }
  const result: Edge[] = []
  for (const building of tree.value.buildings) {
    const child = positions.get(building.key)
    if (!child) continue
    for (const parentKey of building.requires) {
      const parent = positions.get(parentKey)
      if (!parent) continue
      result.push({
        id: `${parentKey}-${building.key}`,
        path: edgePath(parent, child),
      })
    }
  }
  return result
})

function edgePath(parent: { left: number; top: number }, child: { left: number; top: number }): string {
  const parentX = parent.left + 40
  const parentY = parent.top + 80
  const childX = child.left + 40
  const childY = child.top
  const radius = 10

  if (Math.abs(parent.top - child.top) < 2) {
    return `M ${parent.left + 80} ${parent.top + 40} L ${child.left} ${child.top + 40}`
  }

  if (Math.abs(parentX - childX) < 2) {
    return `M ${parentX} ${parentY} L ${childX} ${childY}`
  }

  const midY = Math.round((parentY + childY) / 2)
  const direction = childX > parentX ? 1 : -1
  return [
    `M ${parentX} ${parentY}`,
    `L ${parentX} ${midY - radius}`,
    `Q ${parentX} ${midY} ${parentX + direction * radius} ${midY}`,
    `L ${childX - direction * radius} ${midY}`,
    `Q ${childX} ${midY} ${childX} ${midY + radius}`,
    `L ${childX} ${childY}`,
  ].join(' ')
}

function tooltip(item: CatalogItem, count?: number): string {
  const countText = count === undefined ? '' : ` · ${count}`
  return `${displayName(item)}${countText}`
}
</script>

<style scoped>
.tree-scroll {
  overflow: hidden;
  width: 100%;
  height: 100%;
  scrollbar-width: thin;
  scrollbar-color: #31527a transparent;
}

.tree-canvas {
  position: relative;
  min-width: 100%;
  background:
    radial-gradient(circle at 20% 10%, rgba(46, 94, 160, 0.08), transparent 35%),
    linear-gradient(180deg, #070b14, #050811);
}

.edges {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.building-node {
  position: absolute;
  width: 224px;
  z-index: 1;
}

.building-main {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.icon-shell {
  position: relative;
  flex: none;
  border-radius: 8px;
  border: 1px solid #1d3352;
  background: #0b1424;
  box-shadow: inset 0 0 12px rgba(60, 120, 200, 0.08);
  transition: opacity 160ms ease, filter 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
}

.icon-shell img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 7px;
}

.building-icon {
  width: 80px;
  height: 80px;
}

.building-node.done .building-icon {
  border-color: #3d7fc4;
  box-shadow: 0 0 14px rgba(61, 127, 196, 0.45), inset 0 0 10px rgba(61, 127, 196, 0.12);
}

.building-node.building .building-icon {
  opacity: 0.62;
  animation: pulse 1.4s ease-in-out infinite;
}

.building-node.locked .building-icon {
  opacity: 0.32;
  filter: grayscale(0.85);
}

.building-node.destroyed .building-icon {
  opacity: 0.32;
  filter: grayscale(0.7) sepia(0.3) hue-rotate(-30deg);
}

.unit-grid {
  display: grid;
  grid-template-columns: repeat(3, 42px);
  gap: 5px;
  padding-top: 3px;
}

.unit-icon {
  width: 42px;
  height: 42px;
}

.unit-icon.empty {
  opacity: 0.62;
  filter: grayscale(0.5);
}

.unit-icon.locked {
  opacity: 0.3;
  filter: grayscale(0.95);
}

.unit-icon:not(.locked):not(.empty) {
  border-color: #2c5480;
}

.count-badge {
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

.building-badge {
  color: #fff;
}

.build-progress {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 4px;
  overflow: hidden;
  border-radius: 0 0 7px 7px;
  background: rgba(0, 0, 0, 0.55);
}

.build-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2f9e44, #69db7c);
  transition: width 0.2s linear;
}

.build-progress.indeterminate .build-progress-fill {
  width: 35% !important;
  animation: build-progress-pulse 1.2s ease-in-out infinite;
}

.morph-badges {
  position: absolute;
  left: -5px;
  bottom: -7px;
  display: flex;
  gap: 2px;
}

.morph-badge {
  position: relative;
  width: 26px;
  height: 26px;
  border: 1px solid #4b9bf0;
  border-radius: 5px;
  background: #07101d;
  box-shadow: 0 0 8px rgba(75, 155, 240, 0.4);
}

.morph-badge img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

.morph-count {
  position: absolute;
  right: 1px;
  bottom: 1px;
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  line-height: 1;
  text-shadow:
    0 0 2px #000,
    0 1px 2px #000;
}

.other-node {
  position: absolute;
  z-index: 1;
  width: 224px;
  padding: 8px 10px;
  border: 1px dashed #2b4568;
  border-radius: 10px;
  background: rgba(8, 15, 28, 0.8);
}

.other-label {
  margin-bottom: 6px;
  color: #6f89ad;
  font-size: 11px;
  letter-spacing: 0.08em;
}

.other-grid {
  grid-template-columns: repeat(3, 42px);
}

.unlock-flash {
  animation: unlock-flash 1.2s ease-out;
}

@keyframes build-progress-pulse {
  0%,
  100% {
    opacity: 0.45;
  }
  50% {
    opacity: 1;
  }
}

@keyframes unlock-flash {
  0% {
    filter: brightness(0.9);
    box-shadow: 0 0 0 rgba(120, 200, 255, 0);
  }
  14% {
    filter: brightness(1.9);
    box-shadow: 0 0 28px rgba(120, 200, 255, 0.95), 0 0 10px rgba(120, 200, 255, 0.8);
    transform: scale(1.08);
  }
  100% {
    filter: brightness(1);
    box-shadow: 0 0 0 rgba(120, 200, 255, 0);
    transform: scale(1);
  }
}

@keyframes pulse {
  0%,
  100% {
    box-shadow: 0 0 4px rgba(61, 127, 196, 0.2);
  }
  50% {
    box-shadow: 0 0 16px rgba(61, 127, 196, 0.55);
  }
}
</style>
