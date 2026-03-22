<template>
  <div class="voice-reader-panel" :class="[layout, { 'is-pip': isPip }]" v-show="visible">
    <!-- Header buttons -->
    <div class="voice-reader-header">
      <div class="header-btns">
        <button
          v-if="!isPip"
          class="voice-reader-pip"
          :class="{ disabled: !canPiP }"
          :title="canPiP ? '画中画悬浮窗' : '浏览器不支持 (点击强制尝试)'"
          @click="$emit('pop-out')"
        >
          🗗 {{ !canPiP ? '(不支持)' : '' }}
        </button>
        <button class="voice-reader-close" @click="$emit('close')">&times;</button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="content-body" :class="layout">
      <!-- Steps Display -->
      <div class="steps-info">
        
        <!-- Vertical Layout Steps -->
        <div v-if="layout === 'vertical'" class="steps-list vertical-list">
          <div v-for="(s, idx) in prevSteps" :key="'p'+idx" class="step-other prev-step">
            <span class="step-time">{{ s.time }}</span> {{ s.text }}
          </div>
          <div class="step-main" v-if="currentStep">
            <span class="step-time current-time">{{ currentStep.time }}</span> 
            <span class="step-text">{{ currentStep.text }}</span>
          </div>
          <div class="step-main" v-else>等待开始...</div>
          <div v-for="(s, idx) in nextSteps" :key="'n'+idx" class="step-other next-step">
            <span class="step-time">{{ s.time }}</span> {{ s.text }}
          </div>
        </div>

        <!-- Horizontal Layout Steps -->
        <div v-else class="steps-list horizontal-list">
          <div class="step-main" v-if="currentStep">
            <span class="step-time current-time">{{ currentStep.time }}</span> 
            <span class="step-text">{{ currentStep.text }}</span>
          </div>
          <div class="step-main" v-else>等待开始...</div>
          
          <div class="other-steps-row" v-if="prevSteps.length || nextSteps.length">
            <div class="prev-col">
              <div v-for="(s, idx) in prevSteps" :key="'ph'+idx" class="step-other prev-step">
                {{ s.time }} {{ s.text }}
              </div>
            </div>
            <div class="next-col">
              <div v-for="(s, idx) in nextSteps" :key="'nh'+idx" class="step-other next-step">
                {{ s.time }} {{ s.text }}
              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- Controls and Timer -->
      <div class="controls-timer-row">
        <div id="voice-timer">{{ timerStr }}</div>
        <div class="action-btns">
          <button class="icon-btn play-btn" @click="$emit('toggle-play')" :title="isPlaying ? '暂停' : '继续'">
            {{ isPlaying ? '⏸' : '▶️' }}
          </button>
          <button class="icon-btn reset-btn" @click="$emit('reset')" title="重置">
            ↺
          </button>
        </div>
      </div>
    </div>

    <!-- Segmented Progress Bar at the absolute bottom -->
    <div class="progress-bar-fixed" @click="$emit('timeline-click', $event)">
      <!-- Segment Backgrounds -->
      <div class="segment yellow"></div>
      <div class="segment green"></div>
      <div class="segment red"></div>
      <div class="segment purple"></div>
      
      <!-- Overlays for current step and full timeline -->
      <div class="progress-overlay step" :style="{ width: stepProgress * 100 + '%' }"></div>
      <div class="progress-overlay full" :style="{ width: timelineProgress * 100 + '%' }"></div>
    </div>

    <!-- Hotkey Hint -->
    <div class="hotkey-hint" v-if="!isPip && layout === 'vertical'">
      Alt+ ↑/↓ 播放/重置 | Alt+←/→ 跳步
    </div>
  </div>
</template>

<script setup lang="ts">

interface VoiceStepInfo {
  time: string
  text: string
}

defineProps<{
  visible: boolean
  layout: 'horizontal' | 'vertical'
  timerStr: string
  isPlaying: boolean
  prevSteps: VoiceStepInfo[]
  currentStep: VoiceStepInfo | null
  nextSteps: VoiceStepInfo[]
  stepProgress: number
  timelineProgress: number
  canPiP?: boolean
  isPip?: boolean
}>()

defineEmits<{
  (e: 'close'): void
  (e: 'toggle-play'): void
  (e: 'reset'): void
  (e: 'pop-out'): void
  (e: 'timeline-click', event: MouseEvent): void
}>()
</script>

<style scoped>
.voice-reader-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: rgba(13, 17, 23, 0.95);
  border: 1px solid #30363d;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
  z-index: 1000;
  color: #e6edf3;
  backdrop-filter: blur(10px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.voice-reader-panel.vertical {
  width: 320px;
  padding: 10px 10px 20px 10px;
}

.voice-reader-panel.horizontal {
  width: 540px;
  min-height: 110px;
  padding: 5px 10px 18px 10px;
}

@media all and (display-mode: picture-in-picture) {
  .voice-reader-panel {
    position: static;
    width: 100% !important;
    height: 100% !important;
    border: none;
    border-radius: 0;
  }
}

.voice-reader-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 2px;
}

.header-btns {
  display: flex;
  gap: 8px;
}

.voice-reader-pip, .voice-reader-close {
  background: none;
  border: none;
  color: #8b949e;
  cursor: pointer;
  font-size: 1rem;
  padding: 2px;
  line-height: 1;
}

.voice-reader-pip:hover, .voice-reader-close:hover {
  color: var(--accent-blue);
}

.voice-reader-pip.disabled {
  opacity: 0.3;
}

.content-body {
  display: flex;
  gap: 12px;
  flex: 1;
  overflow: hidden;
}

.content-body.vertical {
  flex-direction: column;
  align-items: center;
}

.content-body.horizontal {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}

.steps-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.step-main {
  font-weight: bold;
  font-size: 1.05rem;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 4px 0;
  border-left: 3px solid var(--accent-green);
  padding-left: 8px;
}

.step-time {
  font-family: 'JetBrains Mono', monospace;
  color: #8b949e;
  margin-right: 6px;
  font-size: 0.85em;
}

.current-time {
  color: var(--accent-orange);
}

.step-other {
  font-size: 0.8rem;
  color: #8b949e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-left: 11px;
}

.prev-step {
  opacity: 0.6;
}

.next-step {
  opacity: 0.8;
}

.other-steps-row {
  display: flex;
  gap: 16px;
  margin-top: 4px;
}

.prev-col, .next-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.controls-timer-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.horizontal .controls-timer-row {
  flex-shrink: 0;
  align-self: flex-end;
  margin-bottom: 8px;
}

#voice-timer {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--green);
}

.action-btns {
  display: flex;
  gap: 6px;
}

.icon-btn {
  background: #238636;
  border: none;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1rem;
}

.icon-btn:hover {
  filter: brightness(1.2);
}

.reset-btn {
  background: #30363d;
}

/* Segmented Progress Bar */
.progress-bar-fixed {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 8px;
  display: flex;
  cursor: pointer;
}

.segment {
  height: 100%;
  width: 25%;
}

.segment.yellow { background: rgba(210, 153, 34, 0.4); }
.segment.green { background: rgba(63, 185, 80, 0.4); }
.segment.red { background: rgba(248, 81, 73, 0.4); }
.segment.purple { background: rgba(163, 113, 247, 0.4); }

.progress-overlay {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  pointer-events: none;
}

.progress-overlay.step {
  background: linear-gradient(90deg, 
    #d29922 0%, #d29922 25%, 
    #3fb950 25%, #3fb950 50%, 
    #f85149 50%, #f85149 75%, 
    #a371f7 75%, #a371f7 100%);
  background-size: 100vw 100%; /* Fix gradient to segments */
  opacity: 0.8;
  z-index: 2;
}

.progress-overlay.full {
  background: rgba(255, 255, 255, 0.3);
  z-index: 3;
}

.hotkey-hint {
  font-size: 0.65rem;
  color: #8b949e;
  text-align: center;
  margin-top: 10px;
}
</style>
