import { reactive, watch } from 'vue'

export interface AppSettings {
  showLibraryWorkers: boolean
}

const STORAGE_KEY = 'sc2-settings'

const defaults: AppSettings = {
  showLibraryWorkers: true,
}

function loadSettings(): AppSettings {
  if (typeof localStorage === 'undefined') return { ...defaults }
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
    return { ...defaults, ...stored }
  } catch {
    return { ...defaults }
  }
}

export const settings = reactive<AppSettings>(loadSettings())

watch(
  settings,
  (value) => {
    if (typeof localStorage === 'undefined') return
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
  },
  { deep: true },
)

export function useSettings() {
  return { settings }
}
