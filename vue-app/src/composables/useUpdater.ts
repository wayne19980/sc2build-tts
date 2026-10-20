import { ref, shallowRef } from 'vue'
import { isTauriRuntime } from './useTauri'

const update = shallowRef<any>(null)
const checking = ref(false)
const installing = ref(false)
const progress = ref(0)
const error = ref('')
const message = ref('')
const downloaded = ref(0)
const total = ref(0)
let autoChecked = false

export function useUpdater() {
  async function checkForUpdates(manual = false): Promise<void> {
    if (!isTauriRuntime() || checking.value || installing.value) return
    checking.value = true
    error.value = ''
    if (manual) message.value = ''
    try {
      const { check } = await import('@tauri-apps/plugin-updater')
      update.value = await check({ timeout: 15000 })
      if (!update.value && manual) {
        message.value = '当前已是最新版本'
        setTimeout(() => {
          if (!update.value) message.value = ''
        }, 3500)
      }
    } catch (exc) {
      if (manual) {
        error.value = exc instanceof Error ? exc.message : String(exc)
      } else {
        console.warn('update check failed', exc)
      }
    } finally {
      checking.value = false
    }
  }

  async function installUpdate(): Promise<void> {
    const pending = update.value
    if (!pending || installing.value) return
    installing.value = true
    error.value = ''
    progress.value = 0
    downloaded.value = 0
    total.value = 0
    try {
      await pending.downloadAndInstall((event: any) => {
        if (event.event === 'Started') {
          total.value = event.data?.contentLength || 0
        } else if (event.event === 'Progress') {
          downloaded.value += event.data?.chunkLength || 0
          if (total.value > 0) {
            progress.value = Math.min(100, (downloaded.value / total.value) * 100)
          }
        } else if (event.event === 'Finished') {
          progress.value = 100
        }
      })
      const { relaunch } = await import('@tauri-apps/plugin-process')
      await relaunch()
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
      installing.value = false
    }
  }

  function dismiss(): void {
    update.value = null
    error.value = ''
    message.value = ''
  }

  async function autoCheck(): Promise<void> {
    if (autoChecked) return
    autoChecked = true
    await new Promise((resolve) => setTimeout(resolve, 5000))
    await checkForUpdates(false)
  }

  return {
    update,
    checking,
    installing,
    progress,
    error,
    message,
    downloaded,
    total,
    checkForUpdates,
    installUpdate,
    dismiss,
    autoCheck,
  }
}
