<template>
  <div class="construction-strip" :class="{ split: strips.length > 1 }">
    <div class="strip-vertical-label">
      <span>PRODUCTION</span>
    </div>

    <div class="strip-rows">
      <div
        v-for="strip in strips"
        :key="strip.key"
        class="strip-row"
        :class="strip.tint ? `tint-${strip.tint}` : undefined"
      >
        <div class="strip-player-badge" :title="strip.playerName">
          <span class="race-dot" :class="raceClass(strip.race)" />
          <span v-if="strip.playerName" class="strip-player-name">{{ strip.playerName }}</span>
        </div>

        <div class="construction-items">
          <div
            v-for="group in strip.groups"
            :key="group.key"
            class="construction-item"
            :title="group.name"
          >
            <div class="item-visual">
              <img v-if="group.icon" :src="group.icon" :alt="group.name" draggable="false" />
              <span v-if="group.count > 1" class="construction-count">{{ group.count }}</span>
            </div>
            <div class="construction-bar" :class="{ indeterminate: group.indeterminate }">
              <div
                class="construction-fill"
                :class="strip.tint ? `fill-${strip.tint}` : (strip.race ? `fill-${strip.race.toLowerCase()}` : '')"
                :style="{ width: `${group.progress * 100}%` }"
              />
            </div>
          </div>
          <div v-if="strip.groups.length === 0" class="task-empty">无建造</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ConstructionStripView, Race } from '../../types-analysis'

defineProps<{
  strips: ConstructionStripView[]
}>()

function raceClass(race?: Race): string {
  if (!race) return ''
  return race.toLowerCase()
}
</script>

<style scoped>
.construction-strip {
  flex: none;
  display: flex;
  align-items: stretch;
  border-top: 1px solid #142238;
  background: rgba(3, 7, 14, 0.94);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
  overflow: hidden;
  user-select: none;
}

.strip-vertical-label {
  flex: none;
  width: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(8, 16, 28, 0.85);
  border-right: 1px solid #142238;
}

.strip-vertical-label span {
  writing-mode: vertical-lr;
  transform: rotate(180deg);
  font-family: 'JetBrains Mono', Consolas, sans-serif;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.18em;
  color: #607b9e;
  text-transform: uppercase;
}

.strip-rows {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.strip-row {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 48px;
  min-width: 0;
  padding: 4px 12px;
  border-bottom: 1px solid rgba(20, 34, 56, 0.6);
}

.strip-row:last-child {
  border-bottom: 0;
}

.strip-player-badge {
  flex: none;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 72px;
  max-width: 104px;
}

.strip-player-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
  font-weight: 600;
  color: #9ab4d6;
}

.strip-row.tint-red .strip-player-name {
  color: #ff9d9d;
}

.strip-row.tint-blue .strip-player-name {
  color: #8ec5ff;
}

.race-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex: none;
  background: #5d789e;
  box-shadow: 0 0 6px currentColor;
}

.race-dot.p {
  background: #e5b948;
  color: #e5b948;
}

.race-dot.t {
  background: #4b9bf0;
  color: #4b9bf0;
}

.race-dot.z {
  background: #ab57e3;
  color: #ab57e3;
}

.strip-row.tint-red .race-dot {
  background: #e5484d;
  color: #e5484d;
}

.strip-row.tint-blue .race-dot {
  background: #4b9bf0;
  color: #4b9bf0;
}

.construction-items {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  overflow-x: auto;
  scrollbar-width: thin;
  scrollbar-color: #243c5e transparent;
  padding: 2px 0;
}

.construction-item {
  position: relative;
  flex: none;
  display: flex;
  flex-direction: column;
  width: 42px;
  background: #060b14;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
}

.item-visual {
  position: relative;
  width: 42px;
  height: 40px;
  background: #08101e;
}

.item-visual img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 3px 3px 0 0;
}

.construction-bar {
  width: 100%;
  height: 4px;
  background: #111a28;
  overflow: hidden;
}

.construction-fill {
  height: 100%;
  background: #46e885;
  box-shadow: 0 0 4px #46e885;
  transition: width 120ms linear;
}

.construction-fill.fill-red {
  background: #ff5c5c;
  box-shadow: 0 0 4px #ff5c5c;
}

.construction-fill.fill-blue {
  background: #4ba2ff;
  box-shadow: 0 0 4px #4ba2ff;
}

.construction-fill.fill-p {
  background: #44ddff;
  box-shadow: 0 0 4px #44ddff;
}

.construction-fill.fill-t {
  background: #4ba2ff;
  box-shadow: 0 0 4px #4ba2ff;
}

.construction-fill.fill-z {
  background: #46e885;
  box-shadow: 0 0 4px #46e885;
}

.construction-bar.indeterminate .construction-fill {
  width: 40% !important;
  animation: construction-pulse 1.2s ease-in-out infinite;
}

.construction-count {
  position: absolute;
  right: 2px;
  bottom: 0px;
  color: #ffffff;
  font-family: 'JetBrains Mono', Consolas, sans-serif;
  font-size: 13px;
  font-weight: 800;
  line-height: 1;
  text-shadow:
    0 0 2px #000,
    0 0 3px #000,
    0 1px 3px #000,
    0 2px 4px #000;
}

.task-empty {
  color: #3f5878;
  font-size: 11px;
  font-style: italic;
  padding: 4px;
}

@keyframes construction-pulse {
  0%,
  100% {
    opacity: 0.35;
  }
  50% {
    opacity: 1;
  }
}
</style>