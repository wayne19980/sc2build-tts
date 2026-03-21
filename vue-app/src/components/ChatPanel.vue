<template>
  <div v-if="messages.length">
    <div class="chat-toggle-row">
      <button class="chat-toggle-btn" type="button" @click="visible = !visible">
        {{ visible ? '收起对局聊天' : '查看对局聊天' }}
      </button>
    </div>
    <div v-show="visible" class="chat-panel">
      <div v-for="(msg, i) in sortedMessages" :key="i" class="chat-item">
        <span class="chat-time">[{{ formatGameTime(msg.time || 0) }}]</span>
        <span class="chat-player">{{ msg.player || `P${msg.pid}` }}</span>
        <span class="chat-target">({{ msg.target || '所有人' }})</span>
        <span class="chat-text">{{ msg.text }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { ChatMessage } from '../types'
import { formatGameTime } from '../utils'

const props = defineProps<{
  messages: ChatMessage[]
}>()

const visible = ref(true)

const sortedMessages = computed(() =>
  [...props.messages].sort((a, b) => (a.time || 0) - (b.time || 0)),
)
</script>

<style scoped>
.chat-toggle-row {
  margin: 0.5rem 0 0.25rem;
  display: flex;
  justify-content: flex-end;
}

.chat-toggle-btn {
  background: transparent;
  border-radius: 6px;
  border: 1px solid var(--border);
  color: var(--accent-blue);
  padding: 0.25rem 0.75rem;
  font-size: 0.8rem;
  cursor: pointer;
}

.chat-toggle-btn:hover {
  background: var(--bg-hover);
  border-color: var(--accent-blue);
}

.chat-panel {
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px solid var(--border);
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  max-height: 240px;
  overflow-y: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  scrollbar-width: thin;
  scrollbar-color: var(--accent-blue) transparent;
}

.chat-item {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.25rem;
}

.chat-item:last-child {
  margin-bottom: 0;
}

.chat-time {
  color: var(--text-muted);
}

.chat-player {
  color: var(--accent-green);
}

.chat-target {
  color: var(--text-muted);
}

.chat-text {
  color: var(--text);
}
</style>
