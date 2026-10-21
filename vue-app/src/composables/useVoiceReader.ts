import { ref } from 'vue'
import type { VoiceStep } from '../types-analysis'
import { GAME_TIME_FACTOR, SC2_FASTER_REAL_FACTOR } from '../utils'

export function useVoiceReader() {
  const steps = ref<VoiceStep[]>([])
  const currentIndex = ref(-1)
  const isRunning = ref(false)
  const currentTime = ref(0) // real elapsed seconds
  const rate = ref(1.2)
  const lang = ref('zh-CN')

  const synth = window.speechSynthesis

  function speak(content: string) {
    if (!content) return
    // Never let old build steps queue up behind the replay clock. At 2x/4x
    // a backlog makes announcements look like they fire on completion.
    synth.cancel()
    const utter = new SpeechSynthesisUtterance(content)
    utter.volume = 1
    utter.rate = rate.value
    utter.lang = lang.value
    synth.speak(utter)
  }

  function indexAt(time: number): number {
    let index = -1
    for (let i = 0; i < steps.value.length; i++) {
      if (time >= steps.value[i].time) index = i
      else break
    }
    return index
  }

  function start() {
    isRunning.value = true
  }

  function stop() {
    isRunning.value = false
    synth.cancel()
  }

  /**
   * Drive voice progression from the replay clock. The caller converts game
   * seconds to the real seconds used by VoiceStep.time.
   */
  function sync(realSeconds: number, options: { speak?: boolean } = {}) {
    const target = Math.max(0, realSeconds)
    const next = indexAt(target)
    const jumped = Math.abs(target - currentTime.value) > 3

    if (jumped || next < currentIndex.value) {
      synth.cancel()
      currentIndex.value = next
      if (isRunning.value && options.speak && next >= 0) {
        speak(steps.value[next].speech)
      }
    } else if (next > currentIndex.value) {
      currentIndex.value = next
      if (isRunning.value && options.speak) {
        speak(steps.value[next].speech)
      }
    }

    currentTime.value = target
  }

  function reset() {
    isRunning.value = false
    currentIndex.value = -1
    currentTime.value = 0
    synth.cancel()
  }

  function loadDisplaySteps(
    items: { time: number; text: string; speech?: string }[],
  ) {
    steps.value = items.map((item) => ({
      time: item.time * SC2_FASTER_REAL_FACTOR,
      text: item.text,
      speech: item.speech || item.text,
    }))
    currentIndex.value = -1
    currentTime.value = 0
    synth.cancel()
  }

  function loadSteps(buildOrder: { start_time: number; text: string }[]) {
    steps.value = buildOrder.map((it) => {
      const realTime = (it.start_time / GAME_TIME_FACTOR) * SC2_FASTER_REAL_FACTOR
      const speech = it.text.replace(/^\d+\s+/, '').replace(/\[.*?s\]/, '')
      return { time: realTime, text: it.text, speech }
    })
    currentIndex.value = -1
    currentTime.value = 0
    synth.cancel()
  }

  return {
    steps,
    currentIndex,
    isRunning,
    currentTime,
    rate,
    lang,
    loadSteps,
    loadDisplaySteps,
    start,
    stop,
    sync,
    reset,
  }
}
