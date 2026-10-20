<template>
  <div class="tree-viewport" :class="{ panning }">
    <div
      ref="host"
      class="scaled-tree"
      @pointerdown="startPan"
      @pointermove="movePan"
      @pointerup="endPan"
      @pointercancel="endPan"
      @wheel="onWheel"
    >
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
          :speed="speed"
        />
      </div>
    </div>
    <div class="tree-controls" @pointerdown.stop @wheel.stop>
      <button title="缩小" @click="zoomBy(0.85)">−</button>
      <button class="zoom-label" title="点击适应窗口" @click="resetView">
        {{ Math.round(scale * 100) }}%
      </button>
      <button title="放大" @click="zoomBy(1.18)">+</button>
      <button class="fit-button" title="适应窗口" @click="resetView">适应</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
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
  speed?: number
}>()

const host = ref<HTMLElement | null>(null)
const hostSize = ref({ width: 0, height: 0 })
const userScale = ref(1)
const panning = ref(false)
let observer: ResizeObserver | null = null
let dragging = false
let dragX = 0
let dragY = 0
let dragLeft = 0
let dragTop = 0

const cellWidth = computed(() => (props.compact ? CELL_W_COMPACT : CELL_W))
const size = computed(() => treeSize(props.race, cellWidth.value))
const fitScale = computed(() => {
  const availableWidth = Math.max(120, hostSize.value.width - 16)
  const availableHeight = Math.max(120, hostSize.value.height - 16)
  if (!hostSize.value.width || !hostSize.value.height) return 1
  return Math.min(1.6, Math.min(availableWidth / size.value.width, availableHeight / size.value.height))
})
const scale = computed(() => {
  const value = fitScale.value * userScale.value
  return Math.min(2.4, Math.max(0.58, value))
})

function clampUserScale(value: number): number {
  return Math.min(3, Math.max(0.5, value))
}

function zoomBy(factor: number) {
  userScale.value = clampUserScale(userScale.value * factor)
}

function centerScroll() {
  if (!host.value) return
  host.value.scrollLeft = Math.max(0, (host.value.scrollWidth - host.value.clientWidth) / 2)
  host.value.scrollTop = Math.max(0, (host.value.scrollHeight - host.value.clientHeight) / 2)
}

function resetView() {
  userScale.value = 1
  void nextTick(centerScroll)
}

function startPan(event: PointerEvent) {
  if (event.button !== 0 || !host.value) return
  dragging = true
  panning.value = true
  dragX = event.clientX
  dragY = event.clientY
  dragLeft = host.value.scrollLeft
  dragTop = host.value.scrollTop
  host.value.setPointerCapture(event.pointerId)
}

function movePan(event: PointerEvent) {
  if (!dragging || !host.value) return
  host.value.scrollLeft = dragLeft - (event.clientX - dragX)
  host.value.scrollTop = dragTop - (event.clientY - dragY)
}

function endPan(event: PointerEvent) {
  if (!dragging) return
  dragging = false
  panning.value = false
  if (host.value?.hasPointerCapture(event.pointerId)) {
    host.value.releasePointerCapture(event.pointerId)
  }
}

function onWheel(event: WheelEvent) {
  if (!event.ctrlKey && !event.metaKey) return
  event.preventDefault()
  zoomBy(event.deltaY < 0 ? 1.12 : 0.89)
}

onMounted(() => {
  if (!host.value) return
  observer = new ResizeObserver((entries) => {
    const entry = entries[0]
    if (!entry) return
    hostSize.value = {
      width: entry.contentRect.width,
      height: entry.contentRect.height,
    }
    void nextTick(centerScroll)
  })
  observer.observe(host.value)
  void nextTick(centerScroll)
})

watch(
  () => [props.race, props.playerId],
  () => {
    userScale.value = 1
    void nextTick(centerScroll)
  },
)

onBeforeUnmount(() => {
  observer?.disconnect()
})
</script>

<style scoped>
.tree-viewport {
  position: relative;
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  overflow: hidden;
}

.scaled-tree {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: auto;
  padding: 8px;
  cursor: grab;
  user-select: none;
  scrollbar-width: thin;
  scrollbar-color: #31527a transparent;
}

.scaled-tree.panning,
.tree-viewport.panning .scaled-tree {
  cursor: grabbing;
}

.scaled-inner {
  flex: none;
  margin: 0 auto;
}

.tree-controls {
  position: absolute;
  right: 10px;
  bottom: 10px;
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 3px;
  border: 1px solid #1d3352;
  border-radius: 7px;
  background: rgba(6, 11, 20, 0.9);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
}

.tree-controls button {
  min-width: 26px;
  height: 24px;
  padding: 0 6px;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: #a8c3e2;
  font-size: 12px;
  cursor: pointer;
}

.tree-controls button:hover {
  background: #16263d;
  color: #eaf4ff;
}

.tree-controls .zoom-label {
  min-width: 42px;
  color: #6f89ad;
  font-size: 10px;
}

.tree-controls .fit-button {
  color: #7fa8d8;
  font-size: 10px;
}
</style>
