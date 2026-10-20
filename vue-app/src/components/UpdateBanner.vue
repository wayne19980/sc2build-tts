<template>
  <div v-if="update || installing || error || message" class="update-banner">
    <template v-if="installing">
      <div class="update-title">正在下载更新…</div>
      <div class="update-progress">
        <div class="update-progress-fill" :style="{ width: `${progress}%` }" />
      </div>
      <div class="update-meta">
        <span>{{ progress.toFixed(0) }}%</span>
        <span v-if="total > 0">
          {{ formatBytes(downloaded) }} / {{ formatBytes(total) }}
        </span>
      </div>
    </template>

    <template v-else-if="update">
      <div class="update-title">发现新版本 v{{ update.version }}</div>
      <div v-if="update.body" class="update-notes">{{ update.body }}</div>
      <div class="update-actions">
        <button class="update-primary" @click="installUpdate">更新并重启</button>
        <button class="update-secondary" @click="dismiss">稍后</button>
      </div>
    </template>

    <template v-else-if="error">
      <div class="update-title">更新检查失败</div>
      <div class="update-error">{{ error }}</div>
      <div class="update-actions">
        <button class="update-secondary" @click="dismiss">关闭</button>
      </div>
    </template>

    <template v-else-if="message">
      <div class="update-title">{{ message }}</div>
      <div class="update-actions">
        <button class="update-secondary" @click="dismiss">关闭</button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { useUpdater } from '../composables/useUpdater'

const {
  update,
  installing,
  progress,
  error,
  message,
  downloaded,
  total,
  installUpdate,
  dismiss,
} = useUpdater()

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
</script>

<style scoped>
.update-banner {
  position: fixed;
  top: 60px;
  right: 16px;
  z-index: 2000;
  width: 320px;
  padding: 12px 14px;
  border: 1px solid #2f6caf;
  border-radius: 10px;
  background: rgba(8, 16, 29, 0.97);
  color: #dcecff;
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(8px);
}

.update-title {
  font-size: 13px;
  font-weight: 700;
}

.update-notes {
  margin-top: 5px;
  max-height: 70px;
  overflow: auto;
  color: #8ca6c8;
  font-size: 11px;
  white-space: pre-wrap;
}

.update-progress {
  height: 6px;
  margin-top: 10px;
  border-radius: 3px;
  background: #14263e;
  overflow: hidden;
}

.update-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2f7fe0, #63b3ff);
  transition: width 0.2s linear;
}

.update-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  color: #6f89ad;
  font-size: 10px;
}

.update-actions {
  display: flex;
  gap: 7px;
  margin-top: 10px;
}

.update-primary,
.update-secondary {
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 11px;
  cursor: pointer;
}

.update-primary {
  border: 1px solid #2f6caf;
  background: #1f5da5;
  color: #fff;
}

.update-secondary {
  border: 1px solid #1d3352;
  background: transparent;
  color: #8ca6c8;
}

.update-error {
  margin-top: 5px;
  color: #ffb4b4;
  font-size: 11px;
  word-break: break-word;
}
</style>
