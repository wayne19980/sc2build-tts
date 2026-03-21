/** SC2 "Faster" game time vs real display time factor */
export const GAME_TIME_FACTOR = 1.4

/** SC2 Faster: 1 game-second ≈ 0.9803 real seconds */
export const SC2_FASTER_REAL_FACTOR = 0.9803

/** Format real seconds as MM:SS */
export function formatRealTime(seconds: number): string {
  const safe = Math.max(0, Math.round(seconds))
  const m = Math.floor(safe / 60)
  const s = safe % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

/** Convert game-internal seconds (frame/16) to display MM:SS */
export function formatGameTime(gameSeconds: number): string {
  const displaySeconds = Math.max(0, Math.round(gameSeconds / GAME_TIME_FACTOR))
  const m = Math.floor(displaySeconds / 60)
  const s = displaySeconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

/** Format unix timestamp to local date string */
export function formatRealWorldTime(timestamp: number): string {
  if (!timestamp && timestamp !== 0) return ''
  const d = new Date(timestamp * 1000)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${hh}:${mm}`
}

/** Format file size in human-readable units */
export function formatFileSize(bytes: number | undefined | null): string {
  if (bytes === undefined || bytes === null) return ''
  const thresh = 1024
  if (bytes < thresh) return `${bytes} B`
  const units = ['KB', 'MB', 'GB', 'TB']
  let u = -1
  let size = bytes
  do {
    size /= thresh
    ++u
  } while (size >= thresh && u < units.length - 1)
  return `${size.toFixed(1)} ${units[u]}`
}

/** Escape HTML special characters */
export function escapeHtml(str: string | null | undefined): string {
  if (str == null) return ''
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}
