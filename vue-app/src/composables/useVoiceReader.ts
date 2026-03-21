import { ref } from 'vue'
import type { VoiceStep } from '../types'
import { GAME_TIME_FACTOR, SC2_FASTER_REAL_FACTOR } from '../utils'

export function useVoiceReader() {
  const steps = ref<VoiceStep[]>([])
  const currentIndex = ref(-1)
  const isRunning = ref(false)
  const visible = ref(false)
  const currentTime = ref(0) // real elapsed seconds
  const rate = ref(2.0)
  const lang = ref('zh-CN')

  let startTime = 0
  let pausedTime = 0
  let timerId: number | null = null
  const synth = window.speechSynthesis

  function speak(content: string) {
    if (!content) return
    const utter = new SpeechSynthesisUtterance(content)
    utter.volume = 1
    utter.rate = rate.value
    utter.lang = lang.value
    synth.speak(utter)
  }

  function updateLoop() {
    if (!isRunning.value) return
    const now = (Date.now() - startTime) / 1000
    currentTime.value = now

    for (let i = 0; i < steps.value.length; i++) {
      if (now >= steps.value[i].time && currentIndex.value < i) {
        currentIndex.value = i
        speak(steps.value[i].speech)
      }
    }

    timerId = requestAnimationFrame(updateLoop)
  }

  /** Game-clock seconds for display (mirrors the in-game timer) */
  const gameClockSeconds = () =>
    Math.round(currentTime.value / SC2_FASTER_REAL_FACTOR)

  /** Progress between current and next step (0–100) */
  function stepProgress(): number {
    const now = currentTime.value
    if (currentIndex.value < steps.value.length - 1) {
      const nextTime = steps.value[currentIndex.value + 1].time
      const prevTime =
        currentIndex.value === -1 ? 0 : steps.value[currentIndex.value].time
      const p = ((now - prevTime) / (nextTime - prevTime)) * 100
      return Math.max(0, Math.min(100, p))
    }
    return 100
  }

  /** Overall timeline progress (0–100) */
  function timelineProgress(): number {
    if (!steps.value.length) return 0
    const totalTime = steps.value[steps.value.length - 1].time + 10
    return (currentTime.value / totalTime) * 100
  }

  function loadSteps(
    buildOrder: { start_time: number; text: string }[],
  ) {
    steps.value = buildOrder.map((it) => {
      const realTime = (it.start_time / GAME_TIME_FACTOR) * SC2_FASTER_REAL_FACTOR
      const speech = it.text.replace(/^\d+\s+/, '').replace(/\[.*?s\]/, '')
      return { time: realTime, text: it.text, speech }
    })
    reset()
  }

  function togglePlay() {
    if (isRunning.value) {
      // pause
      isRunning.value = false
      pausedTime = (Date.now() - startTime) / 1000
      if (timerId) cancelAnimationFrame(timerId)
      synth.pause()
    } else {
      // play / resume
      startTime = Date.now() - pausedTime * 1000
      isRunning.value = true
      updateLoop()
      synth.resume()
    }
  }

  function jumpTo(targetTime: number) {
    synth.cancel()
    pausedTime = Math.max(0, targetTime)
    startTime = Date.now() - pausedTime * 1000
    currentIndex.value = -1
    for (let i = 0; i < steps.value.length; i++) {
      if (pausedTime >= steps.value[i].time) currentIndex.value = i
      else break
    }
    currentTime.value = pausedTime
    if (isRunning.value && currentIndex.value !== -1) {
      speak(steps.value[currentIndex.value].speech)
    }
  }

  function jumpStep(delta: number) {
    const target = currentIndex.value + delta
    if (target >= 0 && target < steps.value.length) {
      jumpTo(steps.value[target].time)
    } else if (target < 0) {
      reset()
    }
  }

  function reset() {
    isRunning.value = false
    pausedTime = 0
    currentIndex.value = -1
    currentTime.value = 0
    if (timerId) cancelAnimationFrame(timerId)
    synth.cancel()
  }

  function stop() {
    isRunning.value = false
    if (timerId) cancelAnimationFrame(timerId)
    synth.cancel()
  }

  function timelineClick(e: MouseEvent) {
    if (!steps.value.length) return
    const el = e.currentTarget as HTMLElement
    if (!el) return
    const rect = el.getBoundingClientRect()
    const x = e.clientX - rect.left
    const percentage = x / rect.width
    const totalTime = steps.value[steps.value.length - 1].time + 10
    jumpTo(totalTime * percentage)
  }

  return {
    steps,
    currentIndex,
    isRunning,
    visible,
    currentTime,
    rate,
    lang,
    gameClockSeconds,
    stepProgress,
    timelineProgress,
    loadSteps,
    togglePlay,
    jumpTo,
    jumpStep,
    reset,
    stop,
    timelineClick,
  }
}
