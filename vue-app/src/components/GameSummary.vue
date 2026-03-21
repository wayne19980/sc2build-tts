<template>
  <div class="game-info" v-if="data">
    <span><strong>地图</strong> {{ data.map_name || 'Unknown' }}</span>
    <span><strong>时长</strong> {{ formatRealTime(data.game_length || 0) }}</span>
    <span v-if="data.client_version"><strong>版本</strong> {{ data.client_version }}</span>
    <span v-if="data.region"><strong>区域</strong> {{ data.region }}</span>
    <span v-if="startStr"><strong>时间</strong> {{ startStr }}</span>
    <span v-if="data.winner"><strong>胜者</strong> {{ data.winner }}</span>
    <span v-if="fileSizeStr"><strong>大小</strong> {{ fileSizeStr }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ReplayData } from '../types'
import { formatRealTime, formatRealWorldTime, formatFileSize } from '../utils'

const props = defineProps<{
  data: ReplayData | null
  fileSize?: number
}>()

const startStr = computed(() =>
  props.data?.start_time ? formatRealWorldTime(props.data.start_time) : '',
)

const fileSizeStr = computed(() =>
  props.fileSize ? formatFileSize(props.fileSize) : '',
)
</script>

<style scoped>
.game-info {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 1rem 1.5rem;
  margin-bottom: 1.5rem;
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
  border: 1px solid var(--border);
}

.game-info span {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.game-info strong {
  color: var(--accent-blue);
}
</style>
