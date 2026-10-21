<template>
  <div class="construction-strip" :class="{ split: strips.length > 1 }">
    <div
      v-for="strip in strips"
      :key="strip.key"
      class="strip-row"
      :class="strip.tint ? `tint-${strip.tint}` : undefined"
    >
      <div class="strip-head">
        <span class="strip-title">正在建造</span>
        <span v-if="strip.playerName" class="strip-player">{{ strip.playerName }}</span>
      </div>
      <div class="construction-items">
        <div
          v-for="group in strip.groups"
          :key="group.key"
          class="construction-item"
          :title="group.name"
        >
          <img v-if="group.icon" :src="group.icon" :alt="group.name" draggable="false" />
          <div class="construction-bar" :class="{ indeterminate: group.indeterminate }">
            <div class="construction-fill" :style="{ width: `${group.progress * 100}%` }" />
          </div>
          <span v-if="group.count > 1" class="construction-count">{{ group.count }}</span>
        </div>
        <div v-if="strip.groups.length === 0" class="task-empty">无</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ConstructionStripView } from '../../types-analysis'

defineProps<{
  strips: ConstructionStripView[]
}>()
</script>

<style scoped>
.construction-strip {
  flex: none;
  display: flex;
  flex-direction: column;
  border-top: 1px solid #16263d;
  background: rgba(6, 11, 20, 0.88);
  overflow: hidden;
}

.strip-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 46px;
  min-width: 0;
  padding: 4px 12px;
}

.construction-strip.split .strip-row + .strip-row {
  border-top: 1px solid #101d2f;
}

.strip-row.tint-red {
  box-shadow: inset 3px 0 0 rgba(229, 72, 77, 0.85);
}

.strip-row.tint-blue {
  box-shadow: inset 3px 0 0 rgba(75, 155, 240, 0.85);
}

.strip-head {
  flex: none;
  display: flex;
  flex-direction: column;
  min-width: 64px;
  color: #8ca6c8;
  font-size: 10px;
  letter-spacing: 0.1em;
}

.strip-player {
  margin-top: 1px;
  max-width: 96px;
  overflow: hidden;
  color: #5f7d9f;
  font-size: 9px;
  letter-spacing: 0;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.strip-row.tint-red .strip-player {
  color: #ff9d9d;
}

.strip-row.tint-blue .strip-player {
  color: #8ec5ff;
}

.construction-items {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
  overflow-x: auto;
  scrollbar-width: thin;
  scrollbar-color: #31527a transparent;
}

.construction-item {
  position: relative;
  flex: none;
  width: 42px;
  height: 42px;
  border: 1px solid #1d3352;
  border-radius: 6px;
  background: #0b1424;
  overflow: hidden;
}

.strip-row.tint-red .construction-item {
  border-color: rgba(229, 72, 77, 0.8);
  background: rgba(229, 72, 77, 0.14);
}

.strip-row.tint-blue .construction-item {
  border-color: rgba(75, 155, 240, 0.8);
  background: rgba(75, 155, 240, 0.14);
}

.construction-item img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 5px;
}

.construction-bar {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 5px;
  background: rgba(0, 0, 0, 0.65);
  overflow: hidden;
}

.construction-fill {
  height: 100%;
  background: #ffffff;
}

.construction-bar.indeterminate .construction-fill {
  width: 35% !important;
  animation: construction-pulse 1.2s ease-in-out infinite;
}

.construction-count {
  position: absolute;
  right: 2px;
  bottom: 6px;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  text-shadow:
    0 0 2px #000,
    0 0 4px #000,
    0 1px 2px #000;
}

.task-empty {
  color: #4f6b8c;
  font-size: 10px;
  font-style: italic;
}

@keyframes construction-pulse {
  0%,
  100% {
    opacity: 0.45;
  }
  50% {
    opacity: 1;
  }
}
</style>