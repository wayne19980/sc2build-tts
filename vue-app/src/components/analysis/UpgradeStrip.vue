<template>
  <div class="upgrade-strip" :class="{ split: rows.length > 1 }">
    <div class="strip-title">升级</div>
    <div class="upgrade-rows">
      <div
        v-for="row in resolvedRows"
        :key="row.key"
        class="upgrade-row"
        :class="row.tint ? `tint-${row.tint}` : undefined"
      >
        <span v-if="row.playerName" class="row-player">{{ row.playerName }}</span>
        <div class="upgrade-list">
          <div
            v-for="entry in row.items"
            :key="entry.item.key"
            class="upgrade-icon"
            :class="{
              done: entry.doneAt !== undefined,
              building: entry.active,
            }"
            :title="tooltip(entry)"
          >
            <img :src="itemIconUrl(entry.item)" :alt="entry.item.name" draggable="false" />
            <span v-if="entry.doneAt !== undefined" class="upgrade-time">
              {{ formatClock(entry.doneAt) }}
            </span>
            <div v-if="entry.active" class="upgrade-progress">
              <div
                class="upgrade-progress-fill"
                :class="{ indeterminate: entry.indeterminate }"
                :style="{ width: `${entry.progress * 100}%` }"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { UpgradeStripRow } from '../../types-analysis'
import { formatClock, itemIconUrl, upgradeItems } from '../../data/catalog'
import {
  collapseUpgrades,
  computeUpgradeStates,
  type CollapsedUpgrade,
} from '../../data/upgrades'
import { useLanguage } from '../../composables/useLanguage'

const props = defineProps<{
  rows: UpgradeStripRow[]
  time: number
}>()

const { displayName } = useLanguage()
const resolvedRows = computed(() =>
  props.rows.map((row) => {
    const states = computeUpgradeStates(row.tech, row.orders, props.time)
    return { ...row, items: collapseUpgrades(upgradeItems(row.race), states) }
  }),
)

function tooltip(entry: CollapsedUpgrade): string {
  const name = displayName(entry.item)
  const target = entry.activeItem ? displayName(entry.activeItem) : ''
  if (entry.doneAt !== undefined) {
    return target
      ? `${name} · ${formatClock(entry.doneAt)} · ${target} 建造中`
      : `${name} · ${formatClock(entry.doneAt)}`
  }
  if (entry.active) return `${target || name} · 建造中`
  return name
}
</script>

<style scoped>
.upgrade-strip {
  display: flex;
  align-items: stretch;
  gap: 12px;
  padding: 6px 12px;
  border-top: 1px solid #16263d;
  background: rgba(6, 11, 20, 0.86);
}

.strip-title {
  flex: none;
  display: flex;
  align-items: center;
  color: #6f89ad;
  font-size: 12px;
  letter-spacing: 0.12em;
}

.upgrade-rows {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.upgrade-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 2px 0;
}

.upgrade-row + .upgrade-row {
  border-top: 1px solid #101d2f;
}

.row-player {
  flex: none;
  width: 70px;
  overflow: hidden;
  color: #5f7d9f;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upgrade-row.tint-red .row-player {
  color: #ff9d9d;
}

.upgrade-row.tint-blue .row-player {
  color: #8ec5ff;
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

.upgrade-row.tint-red .upgrade-icon {
  border-color: rgba(229, 72, 77, 0.75);
  background: rgba(229, 72, 77, 0.12);
}

.upgrade-row.tint-blue .upgrade-icon {
  border-color: rgba(75, 155, 240, 0.75);
  background: rgba(75, 155, 240, 0.12);
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
  background: #ffffff;
}

.upgrade-progress-fill.indeterminate {
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
