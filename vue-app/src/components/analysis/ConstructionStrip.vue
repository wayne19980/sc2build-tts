<template>
  <div class="construction-strip">
    <div class="strip-head">
      <span class="strip-title">正在建造</span>
      <span v-if="playerName" class="strip-player">{{ playerName }}</span>
    </div>
    <div class="task-groups">
      <div v-for="group in groups" :key="group.key" class="task-group">
        <img v-if="group.icon" :src="group.icon" :alt="group.name" draggable="false" />
        <div class="task-body">
          <div class="task-head">
            <span class="task-name">{{ group.name }}</span>
            <span class="task-count">×{{ group.count }}</span>
          </div>
          <div class="task-bars">
            <div
              v-for="(task, index) in group.tasks"
              :key="index"
              class="task-bar"
              :class="{ indeterminate: task.indeterminate }"
            >
              <div class="task-fill" :style="{ width: `${task.progress * 100}%` }" />
            </div>
          </div>
        </div>
      </div>
      <div v-if="groups.length === 0" class="task-empty">无</div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface ConstructionTaskView {
  progress: number
  indeterminate: boolean
}

interface ConstructionGroupView {
  key: string
  name: string
  icon: string
  count: number
  tasks: ConstructionTaskView[]
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
  min-height: 46px;
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

.task-groups {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
  overflow-x: auto;
  scrollbar-width: thin;
  scrollbar-color: #31527a transparent;
}

.task-group {
  flex: none;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 6px;
  border: 1px solid #1d3352;
  border-radius: 7px;
  background: #0b1424;
}

.task-group > img {
  width: 30px;
  height: 30px;
  object-fit: contain;
  border-radius: 4px;
}

.task-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 72px;
}

.task-head {
  display: flex;
  align-items: baseline;
  gap: 4px;
  white-space: nowrap;
}

.task-name {
  color: #cfe3fa;
  font-size: 10px;
}

.task-count {
  color: #d9b45b;
  font-size: 10px;
  font-weight: 700;
}

.task-bars {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.task-bar {
  width: 68px;
  height: 4px;
  border-radius: 2px;
  background: #14263e;
  overflow: hidden;
}

.task-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, #2f7fe0, #63b3ff);
  transition: width 0.2s linear;
}

.task-bar.indeterminate .task-fill {
  width: 35% !important;
  animation: build-pulse 1.2s ease-in-out infinite;
}

.task-empty {
  color: #4f6b8c;
  font-size: 10px;
  font-style: italic;
}

@keyframes build-pulse {
  0%,
  100% {
    opacity: 0.45;
  }
  50% {
    opacity: 1;
  }
}
</style>
