<template>
  <div ref="host" class="scaled-tree">
    <div
      class="scaled-inner"
      :style="{
        width: `${size.width}px`,
        height: `${size.height}px`,
        zoom: scale,
      }"
    >
      <TechTreeCanvas
        :race="race"
        :player-id="playerId"
        :time="time"
        :count-mode="countMode"
        :buildings="buildings"
        :units="units"
        :tech="tech"
        :compact="compact"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import type { EventItem, Race, TechTiming, UnitLifecycle } from '../../types-analysis'
import { CELL_W, CELL_W_COMPACT, treeSize } from '../../data/layout'
import TechTreeCanvas from './TechTreeCanvas.vue'

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

const host = ref<HTMLElement | null>(null)
const hostSize = ref({ width: 0, height: 0 })
let observer: ResizeObserver | null = null

const cellWidth = computed(() => (props.compact ? CELL_W_COMPACT : CELL_W))
const size = computed(() => treeSize(props.race, cellWidth.value))
const scale = computed(() => {
  const availableWidth = Math.max(120, hostSize.value.width - 12)
  const availableHeight = Math.max(120, hostSize.value.height - 12)
  if (!hostSize.value.width || !hostSize.value.height) return 1
  const fit = Math.min(availableWidth / size.value.width, availableHeight / size.value.height)
  return Math.min(1.6, fit)
})

onMounted(() => {
  if (!host.value) return
  observer = new ResizeObserver((entries) => {
    const entry = entries[0]
    if (!entry) return
    hostSize.value = {
      width: entry.contentRect.width,
      height: entry.contentRect.height,
    }
  })
  observer.observe(host.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
})
</script>

<style scoped>
.scaled-tree {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  scrollbar-width: thin;
  scrollbar-color: #31527a transparent;
}

.scaled-inner {
  flex: none;
}
</style>
