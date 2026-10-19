<template>
  <div class="container">
    <header>
      <h1>StarCraft II Replay Analysis - Online</h1>
      <p class="subtitle">修改自ProbiusOfficial/sc2replay_online_analysis</p>
    </header>

    <div v-if="!isPyodideReady" class="init-status">
      <p>{{ pyodideInitStatus }}</p>
      <p class="progress">{{ pyodideInitProgress }}</p>
      <div v-if="pyodideError" class="error-text">{{ pyodideError }}</div>
    </div>

    <template v-else>
      <ReplayUploader v-show="!replayData" @file-selected="onFileSelected" />

      <div v-if="isLoading" class="loading">
        <div class="spinner"></div>
        <p>正在解析录像...</p>
      </div>

      <div v-if="errorMsg" class="error visible">{{ errorMsg }}</div>

      <div v-if="replayData" class="result visible">
        <div class="result-header">
          <GameSummary :data="replayData" :file-size="lastFileSize" />
          <div class="global-voice-settings">
            <div class="setting-item">
              <span>语速: {{ voiceRate.toFixed(1) }}</span>
              <input type="range" min="0.5" max="2" step="0.1" v-model.number="voiceRate" />
            </div>
            <div class="setting-item">
              <button class="layout-toggle-btn"
                @click="voiceLayout = voiceLayout === 'horizontal' ? 'vertical' : 'horizontal'">
                布局: {{ voiceLayout === 'horizontal' ? '横向' : '纵向' }}
              </button>
              <button class="change-replay-btn" @click="resetReplay">更换录像</button>
            </div>
          </div>
        </div>

        <div class="time-mode-toggle">
          <label>
            <input type="checkbox" v-model="showOriginal" />
            显示英文名称
          </label>
          <label>
            <input type="checkbox" v-model="showWorkers" />
            显示农民
          </label>
          <label>
            <input type="checkbox" v-model="mergeSameActions" />
            合并同一秒重复操作
          </label>
        </div>

        <ChatPanel :messages="replayData.chat" />

        <BuildOrderList :data="replayData" :show-original="showOriginal" :show-workers="showWorkers"
          :merge-same-actions="mergeSameActions" @open-voice="onOpenVoice" />
      </div>
    </template>

    <VoiceControlPanel :visible="voiceVisible" :layout="voiceLayout" :timer-str="voiceTimerStr"
      :is-playing="voiceIsRunning" :prev-steps="prevVoiceSteps" :current-step="currentVoiceStepObj"
      :next-steps="nextVoiceSteps" :step-progress="voiceStepProgress() / 100"
      :timeline-progress="voiceTimelineProgress() / 100" :can-pip="isPiPSupported" :is-pip="!!pipWindow"
      @pop-out="onPopOut" @close="voiceVisible = false" @toggle-play="voiceTogglePlay" @reset="voiceReset"
      @timeline-click="voiceTimelineClick" ref="voicePanelRef" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { usePyodide } from './composables/usePyodide'
import { useVoiceReader } from './composables/useVoiceReader'
import { useDocumentPiP } from './composables/useDocumentPiP'
import { getDisplayUnitText } from './composables/useTranslation'
import { formatRealTime, SC2_FASTER_REAL_FACTOR } from './utils'
import type { ReplayData, PlayerData } from './types'

import ReplayUploader from './components/ReplayUploader.vue'
import GameSummary from './components/GameSummary.vue'
import ChatPanel from './components/ChatPanel.vue'
import BuildOrderList from './components/BuildOrderList.vue'
import VoiceControlPanel from './components/VoiceControlPanel.vue'

// Pyodide logic
const {
  initStatus: pyodideInitStatus,
  initProgress: pyodideInitProgress,
  isReady: isPyodideReady,
  isLoading,
  errorMsg: pyodideError,
  init: initPyodide,
  parseReplay,
} = usePyodide()

// UI state
const replayData = ref<ReplayData | null>(null)
const lastFileSize = ref(0)
const errorMsg = ref('')

// Display options
const showOriginal = ref(false)
const showWorkers = ref(false)
const mergeSameActions = ref(false)

// Voice logic
const {
  steps: voiceSteps,
  currentIndex: voiceCurrentIndex,
  isRunning: voiceIsRunning,
  rate: voiceRate,
  lang: voiceLang,
  visible: voiceVisible,
  gameClockSeconds: voiceGameClockSeconds,
  stepProgress: voiceStepProgress,
  timelineProgress: voiceTimelineProgress,
  loadSteps,
  togglePlay: voiceTogglePlay,
  reset: voiceReset,
  timelineClick: voiceTimelineClick,
  jumpStep: voiceJumpStep,
} = useVoiceReader()

const {
  isSupported: isPiPSupported,
  pipWindow,
  requestPiP,
} = useDocumentPiP()

const voicePanelRef = ref<any>(null)
const voicePlayerName = ref('')
const voiceLayout = ref<'horizontal' | 'vertical'>('horizontal')
const currentVoicePlayer = ref<PlayerData | null>(null)

const voiceTimerStr = computed(() => formatRealTime(voiceGameClockSeconds()))

const currentVoiceStepObj = computed(() => {
  const i = voiceCurrentIndex.value
  if (i < 0 || i >= voiceSteps.value.length) return null
  const s = voiceSteps.value[i]
  return {
    time: formatRealTime(s.time / SC2_FASTER_REAL_FACTOR),
    text: s.text
  }
})

const prevVoiceSteps = computed(() => {
  const i = voiceCurrentIndex.value
  if (i <= 0) return []
  const start = Math.max(0, i - 2)
  return voiceSteps.value.slice(start, i).map(s => ({
    time: formatRealTime(s.time / SC2_FASTER_REAL_FACTOR),
    text: s.text
  }))
})

const nextVoiceSteps = computed(() => {
  const i = voiceCurrentIndex.value
  if (i < 0) return voiceSteps.value.slice(0, 2).map(s => ({
    time: formatRealTime(s.time / SC2_FASTER_REAL_FACTOR),
    text: s.text
  }))
  return voiceSteps.value.slice(i + 1, i + 3).map(s => ({
    time: formatRealTime(s.time / SC2_FASTER_REAL_FACTOR),
    text: s.text
  }))
})

watch(showOriginal, (newVal) => {
  voiceLang.value = newVal ? 'en-US' : 'zh-CN'
}, { immediate: true })

onMounted(() => {
  initPyodide()
  setupGlobalKeys()
})

async function onFileSelected(file: File) {
  lastFileSize.value = file.size
  const data = await parseReplay(file)
  if (data) {
    replayData.value = data
  }
}

function resetReplay() {
  replayData.value = null
  voiceReset()
  voiceVisible.value = false
}

function onOpenVoice(player: PlayerData) {
  currentVoicePlayer.value = player
  voicePlayerName.value = player.name
  refreshVoiceSteps()
  voiceVisible.value = true
}

async function onPopOut() {
  if (voicePanelRef.value) {
    const el = voicePanelRef.value.$el
    await requestPiP(el, {
      width: voiceLayout.value === 'horizontal' ? 540 : 320,
      height: voiceLayout.value === 'horizontal' ? 120 : 600,
      fallbackData: {
        get timer() { return voiceTimerStr.value },
        get currentStep() { return currentVoiceStepObj.value },
        get prevSteps() { return prevVoiceSteps.value },
        get nextSteps() { return nextVoiceSteps.value },
        get stepProgress() { return voiceStepProgress() / 100 },
        get timelineProgress() { return voiceTimelineProgress() / 100 },
        get layout() { return voiceLayout.value }
      }
    })
  }
}

function refreshVoiceSteps() {
  if (!currentVoicePlayer.value) return
  const player = currentVoicePlayer.value
  let items = [...(player.build_order || [])]

  if (!showWorkers.value) {
    items = items.filter((it) => !it.is_worker)
  }

  let processed = items.map((it) => ({
    start_time: it.start_time,
    text: getDisplayUnitText(it, showOriginal.value),
  }))

  if (mergeSameActions.value) {
    const merged: typeof processed = []
    let current: (typeof processed)[0] | null = null
    let count = 0
    const flush = () => {
      if (!current) return
      merged.push({
        ...current,
        text: count > 1 ? `${current.text} ×${count}` : current.text,
      })
    }
    processed.forEach((item) => {
      if (!current || current.start_time !== item.start_time || current.text !== item.text) {
        flush()
        current = item
        count = 1
      } else {
        count++
      }
    })
    flush()
    processed = merged
  }

  loadSteps(processed)
}

// Re-generate voice steps if options change while voice reader is active
watch([showOriginal, showWorkers, mergeSameActions], () => {
  if (voiceVisible.value) {
    refreshVoiceSteps()
  }
})

function setupGlobalKeys() {
  window.addEventListener('keydown', (e) => {
    if (!voiceVisible.value) return
    if (e.altKey) {
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        voiceTogglePlay()
      }
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        voiceReset()
      }
      if (e.key === 'ArrowRight') {
        e.preventDefault()
        voiceJumpStep(1)
      }
      if (e.key === 'ArrowLeft') {
        e.preventDefault()
        voiceJumpStep(-1)
      }
    }
  })
}
</script>

<style>
/* CSS tokens and base styles copied from original project */
:root {
  --bg-dark: #0d1117;
  --bg-card: #161b22;
  --bg-hover: #21262d;
  --border: #30363d;
  --text: #e6edf3;
  --text-muted: #8b949e;
  --accent-blue: #58a6ff;
  --accent-green: #3fb950;
  --accent-orange: #d29922;
  --accent-red: #f85149;
  --race-t: #74c0fc;
  --race-p: #b197fc;
  --race-z: #69db7c;
  --panel: #161b22;
  --purple: #a855f7;
  --green: #22c55e;
  --yellow: #eae608;
  --red: #ef4444;
}

body {
  font-family: 'Noto Sans SC', -apple-system, sans-serif;
  background: var(--bg-dark);
  color: var(--text);
  min-height: 100vh;
  line-height: 1.6;
  margin: 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

header {
  text-align: center;
  margin-bottom: 2.5rem;
}

h1 {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.init-status {
  text-align: center;
  padding: 1.5rem;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.init-status .progress {
  margin-top: 1rem;
  color: var(--accent-blue);
}

.error-text {
  color: var(--accent-red);
  margin-top: 1rem;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
}

.loading .spinner {
  display: inline-block;
  width: 32px;
  height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error {
  background: rgba(248, 81, 73, 0.15);
  border: 1px solid var(--accent-red);
  border-radius: 8px;
  padding: 1rem;
  color: var(--accent-red);
  margin-bottom: 1rem;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.global-voice-settings {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
}

.setting-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.setting-item input[type="range"] {
  width: 80px;
}

.layout-toggle-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 0.3rem 0.6rem;
  border-radius: 6px;
  font-size: 0.8rem;
  cursor: pointer;
}

.layout-toggle-btn:hover {
  border-color: var(--purple);
  color: var(--purple);
}

.change-replay-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-muted);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
  white-space: nowrap;
  margin-top: 0.5rem;
}

.change-replay-btn:hover {
  background: var(--bg-hover);
  color: var(--accent-blue);
  border-color: var(--accent-blue);
}

.time-mode-toggle {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.time-mode-toggle label {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}
</style>
