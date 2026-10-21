import type { OverlayAnchor, OverlayState } from '../types-analysis'

const OVERLAY_LABEL = 'overlay'
const OVERLAY_WIDTH = 740
const OVERLAY_HEIGHT = 112

export function isTauriRuntime(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window
}

export async function pickDirectory(): Promise<string | null> {
  if (!isTauriRuntime()) return null
  const { open } = await import('@tauri-apps/plugin-dialog')
  const selected = await open({ directory: true, multiple: false })
  return typeof selected === 'string' ? selected : null
}

export async function pickReplayFile(): Promise<string | null> {
  if (!isTauriRuntime()) return null
  const { open } = await import('@tauri-apps/plugin-dialog')
  const selected = await open({
    multiple: false,
    directory: false,
    filters: [{ name: 'SC2 Replay', extensions: ['SC2Replay', 'sc2replay'] }],
  })
  return typeof selected === 'string' ? selected : null
}

export async function listenDragDrop(
  callback: (paths: string[]) => void,
): Promise<() => void> {
  if (!isTauriRuntime()) return () => {}
  const { getCurrentWindow } = await import('@tauri-apps/api/window')
  return getCurrentWindow().onDragDropEvent((event) => {
    if (event.payload.type === 'drop') callback(event.payload.paths)
  })
}

export async function emitOverlayState(state: OverlayState): Promise<void> {
  if (!isTauriRuntime()) return
  const { emit } = await import('@tauri-apps/api/event')
  await emit('sc2-overlay-state', state)
}

export async function emitOverlayReady(): Promise<void> {
  if (!isTauriRuntime()) return
  const { emit } = await import('@tauri-apps/api/event')
  await emit('sc2-overlay-ready', {})
}

export async function listenOverlayEvent<T>(
  event: string,
  callback: (payload: T) => void,
): Promise<() => void> {
  if (!isTauriRuntime()) return () => {}
  const { listen } = await import('@tauri-apps/api/event')
  return listen<T>(event, (message) => callback(message.payload))
}

export interface OverlayMonitor {
  name: string
  width: number
  height: number
}

export async function listMonitors(): Promise<OverlayMonitor[]> {
  if (!isTauriRuntime()) return []
  const { availableMonitors } = await import('@tauri-apps/api/window')
  const monitors = await availableMonitors()
  return monitors.map((monitor, index) => ({
    name: monitor.name || `显示器 ${index + 1}`,
    width: Math.round(monitor.size.width / (monitor.scaleFactor || 1)),
    height: Math.round(monitor.size.height / (monitor.scaleFactor || 1)),
  }))
}

export async function openOverlayWindow(
  anchor: OverlayAnchor = 'top-center',
  monitorIndex = -2,
): Promise<void> {
  const { WebviewWindow } = await import('@tauri-apps/api/webviewWindow')
  let overlay = await WebviewWindow.getByLabel(OVERLAY_LABEL)

  if (!overlay) {
    overlay = new WebviewWindow(OVERLAY_LABEL, {
      url: 'index.html?overlay=1',
      title: 'SC2 Build Overlay',
      width: OVERLAY_WIDTH,
      height: OVERLAY_HEIGHT,
      transparent: true,
      decorations: false,
      alwaysOnTop: true,
      skipTaskbar: true,
      resizable: false,
      focus: false,
      focusable: false,
      shadow: false,
      visible: false,
    })

    await new Promise<void>((resolve, reject) => {
      overlay?.once('tauri://created', () => resolve())
      overlay?.once('tauri://error', (event) => reject(new Error(String(event))))
    })
  }

  await overlay.setIgnoreCursorEvents(true)
  await overlay.setAlwaysOnTop(true)
  await overlay.setFocusable(false)
  await positionOverlayWindow(anchor, monitorIndex)
  await overlay.show()
}

export async function positionOverlayWindow(
  anchor: OverlayAnchor,
  monitorIndex = -2,
): Promise<void> {
  if (!isTauriRuntime()) return
  const { WebviewWindow } = await import('@tauri-apps/api/webviewWindow')
  const overlay = await WebviewWindow.getByLabel(OVERLAY_LABEL)
  if (!overlay) return

  const { availableMonitors, currentMonitor, primaryMonitor } = await import('@tauri-apps/api/window')
  const { LogicalPosition, LogicalSize } = await import('@tauri-apps/api/dpi')
  const monitors = monitorIndex >= 0 ? await availableMonitors() : []
  const monitor =
    (monitorIndex >= 0 ? monitors[monitorIndex] : null) ??
    (monitorIndex === -2 ? await primaryMonitor() : null) ??
    (await currentMonitor())
  if (!monitor) return

  const scale = monitor.scaleFactor || 1
  const monitorWidth = monitor.size.width / scale
  const monitorHeight = monitor.size.height / scale
  const originX = monitor.position.x / scale
  const originY = monitor.position.y / scale
  const width = Math.min(OVERLAY_WIDTH, Math.max(520, monitorWidth - 48))
  const height = OVERLAY_HEIGHT
  const margin = 8
  const top = anchor === 'top-center' ? 0 : 96
  const bottom = 8

  const x =
    anchor === 'top-right' || anchor === 'bottom-right'
      ? originX + monitorWidth - width - margin
      : anchor === 'top-center'
        ? originX + (monitorWidth - width) / 2
        : originX + margin
  const y =
    anchor === 'bottom-left' || anchor === 'bottom-right'
      ? originY + monitorHeight - height - bottom
      : originY + top

  await overlay.setSize(new LogicalSize(width, height))
  await overlay.setPosition(new LogicalPosition(x, y))
}

export async function hideOverlayWindow(): Promise<void> {
  if (!isTauriRuntime()) return
  const { WebviewWindow } = await import('@tauri-apps/api/webviewWindow')
  const overlay = await WebviewWindow.getByLabel(OVERLAY_LABEL)
  if (overlay) await overlay.hide()
}

export async function closeOverlayWindow(): Promise<void> {
  if (!isTauriRuntime()) return
  const { WebviewWindow } = await import('@tauri-apps/api/webviewWindow')
  const overlay = await WebviewWindow.getByLabel(OVERLAY_LABEL)
  if (overlay) await overlay.close()
}

export const OVERLAY_SHORTCUT = 'CommandOrControl+Shift+O'

export async function registerOverlayShortcut(
  callback: () => void,
): Promise<() => Promise<void>> {
  if (!isTauriRuntime()) return async () => {}
  const { register, unregister } = await import('@tauri-apps/plugin-global-shortcut')
  try {
    await unregister(OVERLAY_SHORTCUT)
  } catch {
    // no existing registration
  }
  await register(OVERLAY_SHORTCUT, (event) => {
    if (event.state === 'Pressed') callback()
  })
  return async () => {
    await unregister(OVERLAY_SHORTCUT)
  }
}
