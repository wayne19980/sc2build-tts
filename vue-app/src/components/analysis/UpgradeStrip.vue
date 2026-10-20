<template>
  <div class="upgrade-strip">
    <div class="strip-title">升级</div>
    <div class="upgrade-list">
      <div
        v-for="item in items"
        :key="item.key"
        class="upgrade-icon"
        :class="{
          done: completedTimes[item.key] !== undefined,
          building: progressMap[item.key] !== undefined,
        }"
        :title="tooltip(item)"
      >
        <img :src="itemIconUrl(item)" :alt="item.name" draggable="false" />
        <span v-if="completedTimes[item.key] !== undefined" class="upgrade-time">
          {{ formatClock(completedTimes[item.key]) }}
        </span>
        <div
          v-if="progressMap[item.key] !== undefined"
          class="upgrade-progress"
          :class="{ indeterminate: progressMap[item.key].indeterminate }"
        >
          <div
            class="upgrade-progress-fill"
            :style="{ width: `${progressMap[item.key].progress * 100}%` }"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { EventItem, Race, TechTiming } from '../../types-analysis'
import { formatClock, itemIconUrl, resolveItem, upgradeItems, type CatalogItem } from '../../data/catalog'
import { useLanguage } from '../../composables/useLanguage'

const props = defineProps<{
  race: Race
  time: number
  tech: TechTiming[]
  orders: EventItem[]
}>()

const { displayName } = useLanguage()
const items = computed(() => upgradeItems(props.race))

const progressMap = computed<Record<string, { progress: number; indeterminate: boolean }>>(() => {
  const completions: Record<string, number> = {}
  for (const timing of props.tech) {
    const item = resolveItem(timing.tech)
    if (!item || item.kind !== 'upgrade') continue
    const current = completions[item.key]
    if (current === undefined || timing.t_sec < current) completions[item.key] = timing.t_sec
  }

  const starts: Record<string, number> = {}
  for (const order of props.orders) {
    if (order.kind !== 'order' || order.player_id === undefined) continue
    const item = resolveItem(order.name)
    if (!item || item.kind !== 'upgrade') continue
    const current = starts[item.key]
    if (current === undefined || order.t_sec > current) starts[item.key] = order.t_sec
  }

  const result: Record<string, { progress: number; indeterminate: boolean }> = {}
  for (const [key, start] of Object.entries(starts)) {
    if (start > props.time) continue
    const done = completions[key]
    if (done !== undefined && done <= props.time) continue
    const progress =
      done !== undefined && done > start
        ? Math.min(1, Math.max(0, (props.time - start) / (done - start)))
        : 0
    result[key] = { progress, indeterminate: done === undefined }
  }
  return result
})

const completedTimes = computed(() => {
  const result: Record<string, number> = {}
  for (const timing of props.tech) {
    if (timing.t_sec > props.time) continue
    const item = resolveItem(timing.tech)
    if (!item || item.kind !== 'upgrade') continue
    if (result[item.key] === undefined) result[item.key] = timing.t_sec
  }
  return result
})

function tooltip(item: CatalogItem): string {
  const time = completedTimes.value[item.key]
  if (time !== undefined) return `${displayName(item)} · ${formatClock(time)}`
  return progressMap.value[item.key] ? `${displayName(item)} · 建造中` : displayName(item)
}
</script>

<style scoped>
.upgrade-strip {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-top: 1px solid #16263d;
  background: rgba(6, 11, 20, 0.86);
}

.strip-title {
  flex: none;
  color: #6f89ad;
  font-size: 12px;
  letter-spacing: 0.12em;
}

.upgrade-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.upgrade-icon {
  position: relative;
  width: 34px;
  height: 34px;
  border-radius: 6px;
  border: 1px solid #1d3352;
  background: #0b1424;
  opacity: 0.34;
  filter: grayscale(0.9);
  transition: opacity 160ms ease, filter 160ms ease, border-color 160ms ease;
}

.upgrade-icon.done {
  opacity: 1;
  filter: none;
  border-color: #3d7fc4;
  box-shadow: 0 0 8px rgba(61, 127, 196, 0.4);
}

.upgrade-icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 5px;
}

.upgrade-progress {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 3px;
  overflow: hidden;
  border-radius: 0 0 5px 5px;
  background: rgba(0, 0, 0, 0.55);
}

.upgrade-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2f9e44, #69db7c);
  transition: width 0.2s linear;
}

.upgrade-progress.indeterminate .upgrade-progress-fill {
  width: 35% !important;
  animation: upgrade-pulse 1.2s ease-in-out infinite;
}

.upgrade-icon.building {
  opacity: 1;
  filter: none;
  border-color: #3d7fc4;
}

@keyframes upgrade-pulse {
  0%,
  100% {
    opacity: 0.45;
  }
  50% {
    opacity: 1;
  }
}

.upgrade-time {
  position: absolute;
  right: -4px;
  bottom: -6px;
  padding: 0 3px;
  border-radius: 4px;
  background: #07101d;
  color: #9fc3ef;
  font-size: 8px;
  line-height: 12px;
  white-space: nowrap;
}
</style>
