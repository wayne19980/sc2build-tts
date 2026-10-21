<template>
  <div v-if="viewMode === 'flow'" class="flow-tree-view">
    <div v-for="row in treeRows" :key="row.id" class="flow-row">
      <div class="flow-grid">
        <div
          v-for="node in row.nodes"
          :key="node.key"
          class="flow-node"
          :class="[node.state, { 'empty-node': !node.units.length && !node.upgrades.length }]"
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
                  v-for="(morph, morphIndex) in node.morphs"
                  :key="`${morph.key}-${morphIndex}`"
                  class="morph-badge"
                  :title="morph.pending ? `${displayName(morph.item)} · 建造中` : `${displayName(morph.item)} ×${morph.count}`"
                >
                  <img :src="iconUrl(morph.item.abbr)" :alt="morph.item.name" draggable="false" />
                  <span v-if="!morph.pending" class="morph-count">{{ morph.count }}</span>
                  <div
                    v-if="morph.progress !== undefined"
                    class="morph-progress"
                    :class="{ indeterminate: morph.indeterminate }"
                  >
                    <div class="morph-progress-fill" :style="{ width: `${morph.progress * 100}%` }" />
                  </div>
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
                <div
                  v-if="unit.progress !== undefined"
                  class="unit-progress"
                  :class="{ indeterminate: unit.indeterminate }"
                >
                  <div class="unit-progress-fill" :style="{ width: `${unit.progress * 100}%` }" />
                </div>
              </div>
            </div>
          </div>

          <div v-if="node.upgrades.length" class="upgrade-row">
            <div
              v-for="chip in node.upgrades"
              :key="chip.key"
              class="upgrade-chip"
              :class="{ done: chip.done, active: chip.active, 'unlock-flash': chip.flash }"
              :title="chipTitle(chip)"
            >
              <img :src="iconUrl(chip.item.icon || chip.item.abbr)" :alt="chip.item.name" draggable="false" />
              <div v-if="chip.active" class="upgrade-chip-bar">
                <div
                  class="upgrade-chip-fill"
                  :class="{ indeterminate: chip.indeterminate }"
                  :style="{ width: `${chip.progress * 100}%` }"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="otherNode" class="flow-row">
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
                <div
                  v-if="unit.progress !== undefined"
                  class="unit-progress"
                  :class="{ indeterminate: unit.indeterminate }"
                >
                  <div class="unit-progress-fill" :style="{ width: `${unit.progress * 100}%` }" />
                </div>
        </div>
      </div>
    </div>
  </div>

  <div v-else class="tree-scroll">
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
                v-for="(morph, morphIndex) in node.morphs"
                :key="`${morph.key}-${morphIndex}`"
                class="morph-badge"
                :title="morph.pending ? `${displayName(morph.item)} · 建造中` : `${displayName(morph.item)} ×${morph.count}`"
              >
                <img :src="iconUrl(morph.item.abbr)" :alt="morph.item.name" draggable="false" />
                <span v-if="!morph.pending" class="morph-count">{{ morph.count }}</span>
                <div
                  v-if="morph.progress !== undefined"
                  class="morph-progress"
                  :class="{ indeterminate: morph.indeterminate }"
                >
                  <div class="morph-progress-fill" :style="{ width: `${morph.progress * 100}%` }" />
                </div>
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
                <div
                  v-if="unit.progress !== undefined"
                  class="unit-progress"
                  :class="{ indeterminate: unit.indeterminate }"
                >
                  <div class="unit-progress-fill" :style="{ width: `${unit.progress * 100}%` }" />
                </div>
            </div>
          </div>
        </div>
        <div v-if="node.upgrades.length" class="upgrade-row">
          <div
            v-for="chip in node.upgrades"
            :key="chip.key"
            class="upgrade-chip"
            :class="{ done: chip.done, active: chip.active, 'unlock-flash': chip.flash }"
            :title="chipTitle(chip)"
          >
            <img :src="iconUrl(chip.item.icon || chip.item.abbr)" :alt="chip.item.name" draggable="false" />
            <div v-if="chip.active" class="upgrade-chip-bar">
              <div
                class="upgrade-chip-fill"
                :class="{ indeterminate: chip.indeterminate }"
                :style="{ width: `${chip.progress * 100}%` }"
              />
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
                <div
                  v-if="unit.progress !== undefined"
                  class="unit-progress"
                  :class="{ indeterminate: unit.indeterminate }"
                >
                  <div class="unit-progress-fill" :style="{ width: `${unit.progress * 100}%` }" />
                </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type {
  EventItem,
  ProductionTaskView,
  Race,
  TechTiming,
  UnitLifecycle,
} from '../../types-analysis'
import { formatClock, iconUrl, resolveItem, techTrees, type CatalogItem } from '../../data/catalog'
import {
  collapseUpgrades,
  computeUpgradeStates,
  UPGRADE_BUILDINGS,
} from '../../data/upgrades'
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
  orders?: EventItem[]
  production?: ProductionTaskView[]
  compact?: boolean
  speed?: number
  viewMode?: 'canvas' | 'flow'
}>()


interface BuildingCounter {
  done: number
  constructing: number
  ever: boolean
  morphs: Record<string, number>
  firstDoneT?: number
}

interface UpgradeChip {
  key: string
  item: CatalogItem
  activeItem?: CatalogItem
  done: boolean
  doneAt?: number
  active: boolean
  progress: number
  indeterminate: boolean
  flash: boolean
}

interface BuildingNode {
  key: string
  x: number
  y: number
  left: number
  top: number
  item: CatalogItem
  state: 'locked' | 'building' | 'done' | 'destroyed'
  count: number
  units: UnitNode[]
  morphs: {
    key: string
    item: CatalogItem
    count: number
    progress?: number
    indeterminate?: boolean
    pending?: boolean
  }[]
  upgrades: UpgradeChip[]
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
  progress?: number
  indeterminate?: boolean
}

const ADDON_OWNERS = ['Barracks', 'Factory', 'Starport'] as const
const ADDON_KEYS = ['TechLab', 'Reactor'] as const
const WORKER_BY_RACE: Record<Race, string> = { P: 'Probe', T: 'SCV', Z: 'Drone' }

/**
 * Tech Lab / Reactor are standalone units in the replay data but they belong
 * to a production building, so resolve `BarracksTechLab` -> Barracks + TechLab.
 */
function addonOf(name: string): { owner: string; key: (typeof ADDON_KEYS)[number] } | null {
  for (const key of ADDON_KEYS) {
    if (!name.endsWith(key)) continue
    const owner = name.slice(0, name.length - key.length)
    return (ADDON_OWNERS as readonly string[]).includes(owner) ? { owner, key } : null
  }
  return null
}

const { displayName } = useLanguage()
const tree = computed(() => techTrees[props.race])
const cellWidth = computed(() => (props.compact ? CELL_W_COMPACT : CELL_W))
const flashWindow = computed(() => 1.2 * Math.max(1, props.speed || 1))

const MORPH_ROOT: Record<string, string> = {
  WarpGate: 'Gateway',
  OrbitalCommand: 'CommandCenter',
  PlanetaryFortress: 'CommandCenter',
  Lair: 'Hatchery',
  Hive: 'Hatchery',
  GreaterSpire: 'Spire',
}

function morphRoot(key: string): string {
  let current = key
  const seen = new Set<string>()
  while (MORPH_ROOT[current] && !seen.has(current)) {
    seen.add(current)
    current = MORPH_ROOT[current]
  }
  return current
}

const buildingStats = computed(() => {
  const counters: Record<string, BuildingCounter> = {}
  const live = new Map<number, { name: string; status: 'building' | 'done' }>()
  const liveBuildings = new Map<string, Set<number>>()
  const addonByBuilding = new Map<number, number>()
  const addonOwner = new Map<number, { owner: string; key: string }>()

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
  const addMorph = (previous: string, next: string) => {
    const target = counter(morphRoot(previous))
    target.ever = true
    target.morphs[next] = (target.morphs[next] || 0) + 1
  }
  const removeMorph = (key: string) => {
    const root = morphRoot(key)
    if (root === key) return
    const target = counter(root)
    target.morphs[key] = Math.max(0, (target.morphs[key] || 0) - 1)
  }
  const addAddon = (owner: string, key: string, at: number) => {
    const target = counter(owner)
    target.ever = true
    target.morphs[key] = (target.morphs[key] || 0) + 1
    if (target.firstDoneT === undefined) target.firstDoneT = at
  }
  const removeAddon = (owner: string, key: string) => {
    const target = counter(owner)
    target.morphs[key] = Math.max(0, (target.morphs[key] || 0) - 1)
  }
  const markTechLab = (owner: string, at: number) => {
    const target = counter(`${owner}TechLab`)
    target.ever = true
    if (target.firstDoneT === undefined) target.firstDoneT = at
  }

  const rememberBuilding = (owner: string, unitId: number) => {
    const ids = liveBuildings.get(owner) || new Set<number>()
    ids.add(unitId)
    liveBuildings.set(owner, ids)
  }
  const forgetBuilding = (owner: string, unitId: number) => {
    liveBuildings.get(owner)?.delete(unitId)
  }
  const attachAddon = (owner: string, key: string, addonUnitId: number, at: number) => {
    const candidates = liveBuildings.get(owner)
    if (!candidates?.size) return
    const buildingUnitId = [...candidates].find((id) => !addonByBuilding.has(id))
    if (buildingUnitId === undefined) return
    addonByBuilding.set(buildingUnitId, addonUnitId)
    addonOwner.set(addonUnitId, { owner, key })
    addAddon(owner, key, at)
  }
  const detachAddon = (addonUnitId: number) => {
    const info = addonOwner.get(addonUnitId)
    if (!info) return
    addonOwner.delete(addonUnitId)
    for (const [buildingUnitId, id] of addonByBuilding) {
      if (id === addonUnitId) {
        addonByBuilding.delete(buildingUnitId)
        break
      }
    }
    removeAddon(info.owner, info.key)
  }
  const detachBuildingAddon = (buildingUnitId: number) => {
    const addonUnitId = addonByBuilding.get(buildingUnitId)
    if (addonUnitId === undefined) return
    addonByBuilding.delete(buildingUnitId)
    const info = addonOwner.get(addonUnitId)
    if (!info) return
    addonOwner.delete(addonUnitId)
    removeAddon(info.owner, info.key)
  }

  for (const event of props.buildings) {
    if (event.player_id !== props.playerId || event.t_sec > props.time) continue
    const addon = addonOf(event.name)
    const detachedAddon = event.name === 'TechLab' || event.name === 'Reactor'
    if (addon || detachedAddon) {
      // Terran addons are separate units but belong to the production
      // building they are attached to. Only attached addons are counted.
      // Lifting a building turns the addon into a plain TechLab/Reactor,
      // landing turns it back into e.g. BarracksReactor.
      const unitId = Number(event.payload?.unit_id)
      const hasUnitId = Number.isFinite(unitId)
      const previous = hasUnitId ? live.get(unitId) : undefined
      if (event.kind === 'unit_morph') {
        if (!hasUnitId) continue
        detachAddon(unitId)
        if (addon) {
          attachAddon(addon.owner, addon.key, unitId, event.t_sec)
          if (addon.key === 'TechLab') markTechLab(addon.owner, event.t_sec)
          live.set(unitId, { name: addon.key, status: 'done' })
        } else {
          live.set(unitId, { name: event.name, status: 'done' })
        }
      } else if (addon && (event.kind === 'build_done' || event.kind === 'unit_born')) {
        if (previous?.status === 'done') continue
        if (hasUnitId) live.set(unitId, { name: addon.key, status: 'done' })
        if (hasUnitId) attachAddon(addon.owner, addon.key, unitId, event.t_sec)
        if (addon.key === 'TechLab') markTechLab(addon.owner, event.t_sec)
      } else if (addon && event.kind === 'build_start') {
        if (hasUnitId) live.set(unitId, { name: addon.key, status: 'building' })
      } else if (event.kind === 'unit_died') {
        if (hasUnitId) {
          detachAddon(unitId)
          live.delete(unitId)
        }
      }
      continue
    }
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
      if (hasUnitId) rememberBuilding(item.key, unitId)
      addDone(item.key, event.t_sec)
    } else if (event.kind === 'unit_morph') {
      if (previous?.status === 'done' && previous.name === item.key) continue
      if (previous?.status === 'building') removeConstructing(previous.name)
      if (previous && previous.name !== item.key) {
        removeMorph(previous.name)
        addMorph(previous.name, item.key)
        if (hasUnitId) {
          forgetBuilding(previous.name, unitId)
          rememberBuilding(item.key, unitId)
        }
      }
      if (hasUnitId) live.set(unitId, { name: item.key, status: 'done' })
      addDone(item.key, event.t_sec)
    } else if (event.kind === 'unit_died') {
      if (previous?.status === 'done') {
        removeDone(previous.name)
        removeMorph(previous.name)
      } else if (previous?.status === 'building') removeConstructing(previous.name)
      if (hasUnitId) {
        forgetBuilding(previous?.name ?? item.key, unitId)
        detachBuildingAddon(unitId)
        live.delete(unitId)
      }
    }
  }

  return counters
})

interface PendingBadge {
  key: string
  item: CatalogItem
  count: number
  progress: number
  indeterminate: boolean
  pending: true
}

const MORPH_TARGETS = new Set([
  'OrbitalCommand',
  'PlanetaryFortress',
  'Lair',
  'Hive',
  'GreaterSpire',
  'WarpGate',
])

const pendingMorphBadges = computed(() => {
  const result = new Map<string, PendingBadge[]>()
  const orders = (props.orders || []).filter(
    (order) => order.player_id === props.playerId && order.kind === 'order',
  )
  for (const event of props.buildings) {
    if (event.player_id !== props.playerId || event.kind !== 'unit_morph') continue
    if (!MORPH_TARGETS.has(event.name)) continue
    const order = orders
      .filter((item) => item.name === event.name && item.t_sec < event.t_sec)
      .sort((a, b) => b.t_sec - a.t_sec)[0]
    if (!order) continue
    if (props.time < order.t_sec || props.time >= event.t_sec) continue
    const item = resolveItem(event.name)
    if (!item) continue
    const root = morphRoot(event.name)
    const list = result.get(root) || []
    list.push({
      key: item.key,
      item,
      count: 1,
      progress: Math.min(
        1,
        Math.max(0, (props.time - order.t_sec) / (event.t_sec - order.t_sec)),
      ),
      indeterminate: false,
      pending: true,
    })
    result.set(root, list)
  }
  return result
})

const pendingAddonBadges = computed(() => {
  const result = new Map<string, PendingBadge[]>()
  const starts = new Map<number, { name: string; start: number }>()
  for (const event of props.buildings) {
    if (event.player_id !== props.playerId) continue
    const addon = addonOf(event.name)
    if (!addon) continue
    const unitId = Number(event.payload?.unit_id)
    if (!Number.isFinite(unitId)) continue
    if (event.kind === 'build_start') {
      starts.set(unitId, { name: event.name, start: event.t_sec })
      continue
    }
    if (event.kind !== 'build_done' && event.kind !== 'unit_born') continue
    const start = starts.get(unitId)
    starts.delete(unitId)
    if (!start) continue
    if (props.time < start.start || props.time >= event.t_sec) continue
    const item = resolveItem(addon.key)
    if (!item) continue
    const list = result.get(addon.owner) || []
    list.push({
      key: item.key,
      item,
      count: 1,
      progress: Math.min(
        1,
        Math.max(0, (props.time - start.start) / (event.t_sec - start.start)),
      ),
      indeterminate: false,
      pending: true,
    })
    result.set(addon.owner, list)
  }
  return result
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

const unitProgress = computed(() => {
  const result = new Map<string, { progress: number; indeterminate: boolean }>()
  for (const task of props.production || []) {
    if (task.start > props.time) continue
    if (task.done !== null && task.done <= props.time) continue
    const progress =
      task.done !== null && task.done > task.start
        ? Math.min(1, Math.max(0, (props.time - task.start) / (task.done - task.start)))
        : 0
    const current = result.get(task.key)
    if (!current || progress > current.progress) {
      result.set(task.key, { progress, indeterminate: task.done === null })
    }
  }
  return result
})

const unitItems = computed(() => {
  const grouped = new Map<string, UnitNode[]>()
  const time = props.time
  for (const group of tree.value.unitGroups) {
    const units: UnitNode[] = []
    const prodDoneT = buildingStats.value[group.group]?.firstDoneT
    for (const unit of group.units) {
      const item = resolveItem(unit.key)
      if (!item) continue

      let techDoneT: number | undefined = undefined
      if (unit.requiresAny.length === 0) {
        techDoneT = prodDoneT
      } else {
        const times = unit.requiresAny
          .map((requirement) => buildingStats.value[requirement]?.firstDoneT)
          .filter((value): value is number => value !== undefined)
        if (times.length > 0) {
          techDoneT = Math.min(...times)
        }
      }

      const unlocked = prodDoneT !== undefined && techDoneT !== undefined
      const unlockAt = unlocked ? Math.max(prodDoneT!, techDoneT!) : undefined
      const flash = Boolean(
        unlocked &&
          unlockAt !== undefined &&
          time >= unlockAt &&
          time - unlockAt < flashWindow.value,
      )

      const task = unitProgress.value.get(item.key)
      units.push({
        key: item.key,
        item,
        count: unitCounts.value[item.key] || 0,
        unlocked,
        flash,
        progress: task?.progress,
        indeterminate: task?.indeterminate,
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
    } else if (event.kind === 'unit_died' && event.t_sec <= props.time) {
      tasks.delete(unitId)
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

const upgradeStates = computed(() => {
  const orders = (props.orders || []).filter((order) => order.player_id === props.playerId)
  return computeUpgradeStates(props.tech, orders, props.time)
})

const buildingUpgrades = computed(() => {
  const map = UPGRADE_BUILDINGS[props.race]
  const result: Record<string, UpgradeChip[]> = {}
  for (const [buildingKey, keys] of Object.entries(map)) {
    const items = keys
      .map((key) => resolveItem(key))
      .filter((item): item is CatalogItem => Boolean(item))
    const chips: UpgradeChip[] = collapseUpgrades(items, upgradeStates.value).map(
      (collapsed) => {
        const doneAt = collapsed.doneAt
        return {
          key: collapsed.item.key,
          item: collapsed.item,
          activeItem: collapsed.activeItem,
          done: doneAt !== undefined,
          doneAt,
          active: collapsed.active,
          progress: collapsed.progress,
          indeterminate: collapsed.indeterminate,
          flash:
            !collapsed.active &&
            doneAt !== undefined &&
            props.time >= doneAt &&
            props.time - doneAt < flashWindow.value,
        }
      },
    )
    if (chips.length) result[buildingKey] = chips
  }
  return result
})

const buildingNodes = computed<BuildingNode[]>(() => {
  const treeKeys = new Set(tree.value.buildings.map((building) => building.key))
  const baseKey = tree.value.buildings.find((building) => building.requires.length === 0)?.key
  const workerItem = resolveItem(WORKER_BY_RACE[props.race])
  return tree.value.buildings.map((building) => {
    const stats = buildingStats.value[building.key]
    let state: BuildingNode['state'] = 'locked'
    if (stats?.done) state = 'done'
    else if (stats?.constructing) state = 'building'
    else if (stats?.ever) state = 'destroyed'

    return {
      key: building.key,
      x: building.x,
      y: building.y,
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
        props.time - stats.firstDoneT < flashWindow.value,
      units: (() => {
        const morphUnits = Object.keys(MORPH_ROOT)
          .filter((key) => key !== building.key && morphRoot(key) === building.key)
          .flatMap((key) => unitItems.value.get(key) || [])
        const ownUnits = [...(unitItems.value.get(building.key) || []), ...morphUnits]
        return building.key === baseKey && workerItem
          ? [
              {
                key: workerItem.key,
                item: workerItem,
                count: unitCounts.value[workerItem.key] || 0,
                unlocked: true,
                flash: false,
                progress: unitProgress.value.get(workerItem.key)?.progress,
                indeterminate: unitProgress.value.get(workerItem.key)?.indeterminate,
              },
              ...ownUnits,
            ]
          : ownUnits
      })(),
      upgrades: buildingUpgrades.value[building.key] || [],
      morphs: (() => {
        const completed = Object.entries(stats?.morphs || {})
          .map(([key, count]) => {
            const item = resolveItem(key)
            return item && item.kind === 'building' && !treeKeys.has(key) && count > 0
              ? { key, item, count }
              : null
          })
          .filter(
            (entry): entry is { key: string; item: CatalogItem; count: number } =>
              entry !== null,
          )
        return [
          ...completed,
          ...(pendingMorphBadges.value.get(building.key) || []),
          ...(pendingAddonBadges.value.get(building.key) || []),
        ]
      })(),
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
        flash: unlockAt !== undefined && props.time >= unlockAt && props.time - unlockAt < flashWindow.value,
      }
    })
    .filter((unit): unit is UnitNode => unit !== null)

  return {
    left: MARGIN + maxX * cellWidth.value,
    top: MARGIN + (maxY + 1) * ROW_H,
    units,
  }
})

interface RowGroup {
  id: string
  nodes: BuildingNode[]
}

const treeRows = computed<RowGroup[]>(() => {
  const rows = new Map<number, BuildingNode[]>()
  for (const node of buildingNodes.value) {
    const nodes = rows.get(node.y) || []
    nodes.push(node)
    rows.set(node.y, nodes)
  }

  return [...rows.entries()]
    .sort(([a], [b]) => a - b)
    .map(([y, nodes]) => ({
      id: `row-${y}`,
      nodes: [...nodes].sort((a, b) => {
        const aEmpty = a.units.length === 0 && a.upgrades.length === 0 ? 1 : 0
        const bEmpty = b.units.length === 0 && b.upgrades.length === 0 ? 1 : 0
        return aEmpty - bEmpty || a.x - b.x
      }),
    }))
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
      const parent = positions.get(parentKey) ?? positions.get(morphRoot(parentKey))
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
  const parentX = parent.left + 32
  const parentY = parent.top + 64
  const childX = child.left + 32
  const childY = child.top
  const radius = 10

  if (Math.abs(parent.top - child.top) < 2) {
    return `M ${parent.left + 64} ${parent.top + 32} L ${child.left} ${child.top + 32}`
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

function chipTitle(chip: UpgradeChip): string {
  const name = displayName(chip.activeItem ?? chip.item)
  if (chip.active) return `${name} · 建造中`
  if (chip.doneAt !== undefined) return `${name} · ${formatClock(chip.doneAt)}`
  return name
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
  width: 220px;
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  column-gap: 8px;
  align-items: start;
  z-index: 1;
}

.building-main {
  display: contents;
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
  width: 64px;
  height: 64px;
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
  opacity: 0.62;
  filter: grayscale(0.35) sepia(0.25) hue-rotate(-25deg) brightness(0.85);
  border-color: #7a3d3d;
  box-shadow: inset 0 0 12px rgba(180, 60, 60, 0.16);
}

.unit-grid {
  display: grid;
  grid-template-columns: repeat(4, 34px);
  gap: 4px;
  padding-top: 3px;
}

.unit-icon {
  width: 34px;
  height: 34px;
  transition: opacity 220ms ease, filter 220ms ease, border-color 220ms ease, box-shadow 220ms ease, transform 220ms ease;
}

.unit-icon.locked {
  opacity: 0.22;
  filter: grayscale(1) brightness(0.55) contrast(0.9);
  border: 1px dashed rgba(60, 95, 140, 0.35);
  background: rgba(4, 8, 16, 0.85);
}

.unit-icon.empty:not(.locked) {
  opacity: 0.72;
  filter: grayscale(0.2) brightness(0.92);
  border: 1px solid rgba(75, 155, 240, 0.45);
  background: rgba(8, 18, 34, 0.85);
}

.unit-icon:not(.locked):not(.empty) {
  opacity: 1;
  filter: none;
  border: 1.5px solid #58a6ff;
  background: #091528;
  box-shadow: 0 0 10px rgba(88, 166, 255, 0.35), inset 0 0 8px rgba(88, 166, 255, 0.15);
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
  background: #ffffff;
}

.build-progress.indeterminate .build-progress-fill {
  width: 35% !important;
  animation: build-progress-pulse 1.2s ease-in-out infinite;
}


.unit-progress,
.morph-progress {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.65);
}

.unit-progress {
  height: 3px;
  border-radius: 0 0 6px 6px;
}

.morph-progress {
  height: 2px;
  border-radius: 0 0 4px 4px;
}

.unit-progress-fill,
.morph-progress-fill {
  height: 100%;
  background: #ffffff;
}

.unit-progress.indeterminate .unit-progress-fill,
.morph-progress.indeterminate .morph-progress-fill {
  width: 35% !important;
  animation: build-progress-pulse 1.2s ease-in-out infinite;
}

/* Upgrades researched by this building, echoed from the upgrade strip. */
.upgrade-row {
  grid-column: 2;
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  margin-top: 2px;
  max-width: 148px;
}

.upgrade-chip {
  position: relative;
  width: 28px;
  height: 28px;
  flex: none;
  border: 1px solid #1d3352;
  border-radius: 5px;
  background: #0b1424;
  opacity: 0.3;
  filter: grayscale(0.9);
  transition: opacity 160ms ease, filter 160ms ease, border-color 160ms ease;
}

.upgrade-chip img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

.upgrade-chip.done {
  opacity: 1;
  filter: none;
  border-color: #3d7fc4;
}

.upgrade-chip.active {
  opacity: 1;
  filter: none;
  border-color: #9fc3ef;
}

.upgrade-chip-bar {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 3px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.6);
}

.upgrade-chip-fill {
  height: 100%;
  background: #ffffff;
}

.upgrade-chip-fill.indeterminate {
  width: 35% !important;
  animation: build-progress-pulse 1.2s ease-in-out infinite;
}

.morph-badges {
  position: absolute;
  left: -6px;
  top: -6px;
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
  grid-template-columns: repeat(4, 34px);
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
    filter: grayscale(1) brightness(0.6);
    box-shadow: 0 0 0 rgba(120, 200, 255, 0);
    transform: scale(0.95);
  }
  22% {
    filter: brightness(2.1) contrast(1.2);
    box-shadow: 0 0 30px rgba(120, 200, 255, 0.95), 0 0 10px #ffffff;
    transform: scale(1.16);
    border-color: #8ed0ff;
    z-index: 10;
  }
  100% {
    filter: brightness(1);
    box-shadow: 0 0 8px rgba(75, 155, 240, 0.3);
    transform: scale(1);
    z-index: 1;
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

/* Flow View (Adaptive icon grid, same nodes as the full canvas) */
.flow-tree-view {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px 24px;
  display: flex;
  flex-direction: column;
  user-select: none;
}

.flow-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.flow-row + .flow-row {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(75, 155, 240, 0.1);
}

.flow-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 6px;
  align-items: flex-start;
}

.flow-node {
  display: grid;
  flex: 0 0 220px;
  grid-template-columns: 64px minmax(0, 1fr);
  column-gap: 8px;
  align-items: start;
  min-width: 0;
  width: 220px;
}

.flow-node.empty-node {
  flex-basis: 64px;
  width: 64px;
}

.flow-node.done .building-icon {
  border-color: #3d7fc4;
  box-shadow: 0 0 14px rgba(61, 127, 196, 0.45), inset 0 0 10px rgba(61, 127, 196, 0.12);
}

.flow-node.locked .building-icon {
  opacity: 0.32;
  filter: grayscale(0.85);
}

.flow-node.building .building-icon {
  opacity: 0.62;
  animation: pulse 1.4s ease-in-out infinite;
}

.flow-node.destroyed .building-icon {
  opacity: 0.62;
  filter: grayscale(0.35) sepia(0.25) hue-rotate(-25deg) brightness(0.85);
  border-color: #7a3d3d;
  box-shadow: inset 0 0 12px rgba(180, 60, 60, 0.16);
}

</style>
