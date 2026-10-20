<template>
  <div class="construction-strip">
    <div class="strip-head">
      <span class="strip-title">正在建造</span>
      <span v-if="playerName" class="strip-player">{{ playerName }}</span>
    </div>
    <div class="construction-items">
      <div
        v-for="group in groups"
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
      <div v-if="groups.length === 0" class="task-empty">无</div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface ConstructionGroupView {
  key: string
  name: string
  icon: string
  count: number
  progress: number
  indeterminate: boolean
}

defineProps<{
  playerName: string
  groups: ConstructionGroupView[]
}>()
</script>

<style scoped>
.construction-strip {
  flex: none;
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 48px;
  padding: 5px 12px;
  border-top: 1px solid #16263d;
  background: rgba(6, 11, 20, 0.88);
  overflow: hidden;
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
  color: #5f7d9f;
  font-size: 9px;
  letter-spacing: 0;
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
  background: linear-gradient(90deg, #2f9e44, #69db7c);
  transition: width 0.2s linear;
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
