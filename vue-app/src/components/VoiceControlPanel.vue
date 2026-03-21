<template>
  <div class="voice-reader-panel" v-show="visible">
    <div class="voice-reader-header">
      <h3>Build Order Reader - {{ playerName }}</h3>
      <button class="voice-reader-close" @click="$emit('close')">&times;</button>
    </div>
    <div id="voice-timer">{{ timerStr }}</div>

    <div class="voice-queue">
      <div class="voice-step past">{{ getStepText(currentIndex - 2) }}</div>
      <div class="voice-step past">{{ getStepText(currentIndex - 1) }}</div>
      <div class="voice-step active">
        {{ currentIndex === -1 ? '准备就绪' : getStepText(currentIndex) }}
      </div>
      <div class="voice-step future">{{ getStepText(currentIndex + 1) }}</div>
      <div class="voice-step future">{{ getStepText(currentIndex + 2) }}</div>
    </div>

    <div class="voice-step-progress">
      <div id="voice-step-bar" :style="{ width: stepProgress + '%' }"></div>
    </div>

    <div class="voice-timeline" @click="(e) => $emit('timeline-click', e)">
      <div id="voice-timeline-bar" :style="{ width: timelineProgress + '%' }"></div>
    </div>

    <div class="voice-controls">
      <button class="voice-btn voice-btn-play" @click="$emit('toggle-play')">
        {{ isRunning ? '暂停' : '继续' }} (Alt+↑)
      </button>
      <button class="voice-btn voice-btn-reset" @click="$emit('reset')">
        重置 (Alt+↓)
      </button>
    </div>

    <div class="voice-settings">
      <div class="voice-setting-row">
        <span>语速</span>
        <input
          type="range"
          min="1"
          max="4"
          step="0.2"
          :value="rate"
          @input="onRateInput"
        />
      </div>
      <div class="voice-setting-row">
        <span>语言</span>
        <select :value="lang" @change="onLangChange">
          <option value="zh-CN">中文 (简体)</option>
          <option value="en-US">English (US)</option>
        </select>
      </div>
      <div style="font-size: 0.65rem; margin-top: 0.25rem">
        Alt+↑/↓ 播放/重置 | Alt+←/→ 跳步
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { VoiceStep } from '../types'

const props = defineProps<{
  visible: boolean
  playerName: string
  steps: VoiceStep[]
  currentIndex: number
  isRunning: boolean
  gameClockSeconds: number
  stepProgress: number
  timelineProgress: number
  rate: number
  lang: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'toggle-play'): void
  (e: 'reset'): void
  (e: 'update:rate', val: number): void
  (e: 'update:lang', val: string): void
  (e: 'timeline-click', event: MouseEvent): void
}>()

const timerStr = computed(() => {
  const m = Math.floor(props.gameClockSeconds / 60)
    .toString()
    .padStart(2, '0')
  const s = Math.floor(props.gameClockSeconds % 60)
    .toString()
    .padStart(2, '0')
  return `${m}:${s}`
})

function getStepText(idx: number) {
  if (idx < 0 || idx >= props.steps.length) return ''
  return props.steps[idx].text
}

function onRateInput(e: Event) {
  const val = parseFloat((e.target as HTMLInputElement).value)
  emit('update:rate', val)
}

function onLangChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  emit('update:lang', val)
}
</script>

<style scoped>
.voice-reader-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 340px;
  background: rgba(22, 27, 34, 0.98);
  border: 1px solid #30363d;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
  padding: 18px;
  z-index: 1000;
  color: #e6edf3;
  backdrop-filter: blur(10px);
}

.voice-reader-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  border-bottom: 1px solid #30363d;
  padding-bottom: 8px;
}

.voice-reader-header h3 {
  margin: 0;
  font-size: 0.95rem;
  color: var(--purple);
  line-height: 1.2;
  padding-right: 20px;
}

.voice-reader-close {
  background: none;
  border: none;
  color: #8b949e;
  font-size: 1.4rem;
  cursor: pointer;
  line-height: 1;
}

#voice-timer {
  text-align: center;
  font-size: 1.8rem;
  font-weight: bold;
  margin: 12px 0;
  color: var(--accent-green);
  font-family: 'JetBrains Mono', monospace;
}

.voice-queue {
  min-height: 180px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 10px;
  overflow: hidden;
}

.voice-step {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.82rem;
  transition: all 0.2s;
  border: 1px solid transparent;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.voice-step.past {
  color: #484f58;
  opacity: 0.6;
}

.voice-step.active {
  background: rgba(168, 85, 247, 0.15);
  border-color: var(--purple);
  color: #fff;
  font-weight: bold;
  font-size: 1rem;
  box-shadow: 0 0 10px rgba(168, 85, 247, 0.2);
}

.voice-step.future {
  color: #8b949e;
}

.voice-step-progress {
  height: 4px;
  background: #21262d;
  border-radius: 2px;
  overflow: hidden;
}

#voice-step-bar {
  height: 100%;
  background: linear-gradient(
    90deg,
    var(--yellow) 0%,
    var(--green) 33%,
    var(--red) 66%,
    var(--purple) 100%
  );
  background-size: 340px 100%;
  width: 0%;
  transition: width 0.1s linear;
}

.voice-timeline {
  height: 8px;
  background: #21262d;
  border-radius: 4px;
  margin: 20px 0;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

#voice-timeline-bar {
  height: 100%;
  background: var(--accent-blue);
  width: 0%;
  border-radius: 4px;
  opacity: 0.5;
}

.voice-controls {
  display: flex;
  gap: 12px;
  margin: 15px 0;
}

.voice-btn {
  flex: 1;
  padding: 10px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  transition: transform 0.1s;
}

.voice-btn:active {
  transform: scale(0.98);
}

.voice-btn-play {
  background: var(--purple);
  color: white;
}

.voice-btn-reset {
  background: #30363d;
  color: #e6edf3;
}

.voice-settings {
  border-top: 1px solid #30363d;
  padding-top: 12px;
  font-size: 0.75rem;
  color: #8b949e;
}

.voice-setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.voice-setting-row select,
.voice-setting-row input[type='range'] {
  background: #0d1117;
  border: 1px solid #30363d;
  color: white;
  padding: 2px 5px;
  border-radius: 4px;
}

.voice-setting-row input[type='range'] {
  height: 4px;
}
</style>
