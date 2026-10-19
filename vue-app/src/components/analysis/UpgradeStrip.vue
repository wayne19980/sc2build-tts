<template>
  <div class="upgrade-strip">
    <div class="strip-title">升级</div>
    <div class="upgrade-list">
      <div
        v-for="item in items"
        :key="item.key"
        class="upgrade-icon"
        :class="{ done: completedTimes[item.key] !== undefined }"
        :title="tooltip(item)"
      >
        <img :src="iconUrl(item.abbr)" :alt="item.name" draggable="false" />
        <span v-if="completedTimes[item.key] !== undefined" class="upgrade-time">
          {{ formatClock(completedTimes[item.key]) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Race, TechTiming } from '../../types-analysis'
import { formatClock, iconUrl, resolveItem, upgradeItems, type CatalogItem } from '../../data/catalog'

const props = defineProps<{
  race: Race
  time: number
  tech: TechTiming[]
}>()

const items = computed(() => upgradeItems(props.race))

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
  return time === undefined ? `${item.name} / ${item.nameZh}` : `${item.name} / ${item.nameZh} · ${formatClock(time)}`
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
