<template>
  <div
    class="drop-zone"
    :class="{ dragover: isDragover }"
    @click="triggerInput"
    @dragover.prevent="isDragover = true"
    @dragleave="isDragover = false"
    @drop.prevent="onDrop"
  >
    <div class="icon">📁</div>
    <p>将录像文件拖放到此处，或点击选择文件</p>
    <p class="hint">支持 .SC2Replay 格式 · 解析在浏览器内完成，文件不会上传</p>
    <input
      ref="fileRef"
      type="file"
      accept=".SC2Replay,.sc2replay"
      @change="onFileChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'file-selected', file: File): void
}>()

const isDragover = ref(false)
const fileRef = ref<HTMLInputElement | null>(null)

function triggerInput() {
  fileRef.value?.click()
}

function onDrop(e: DragEvent) {
  isDragover.value = false
  const file = e.dataTransfer?.files[0]
  if (file && file.name.toLowerCase().endsWith('.sc2replay')) {
    emit('file-selected', file)
  }
}

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    emit('file-selected', file)
  }
  target.value = ''
}
</script>

<style scoped>
.drop-zone {
  border: 2px dashed var(--border);
  border-radius: 12px;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--bg-card);
  margin-bottom: 2rem;
}

.drop-zone:hover,
.drop-zone.dragover {
  border-color: var(--accent-blue);
  background: var(--bg-hover);
}

.drop-zone .icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.7;
}

.drop-zone p {
  color: var(--text-muted);
  font-size: 0.95rem;
}

.drop-zone .hint {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  opacity: 0.8;
}

input[type='file'] {
  display: none;
}
</style>
