import { translationData } from '../data/translations'
import type { RawBuildItem } from '../types'

/** Get the display text for a build item, respecting showOriginal mode */
export function getDisplayUnitText(item: RawBuildItem, showOriginal: boolean): string {
  const name = item.unit || ''

  if (showOriginal) {
    return name
  }

  // Search translation tables in priority order
  let zh: string | null = null

  if (translationData.upgrade[name]) {
    zh = translationData.upgrade[name].zh
  }
  if (!zh && translationData.unit[name]) {
    zh = translationData.unit[name].zh
  }
  if (!zh && translationData.build[name]) {
    zh = translationData.build[name].zh
  }
  if (!zh) {
    for (const group of Object.values(translationData.change)) {
      if (group && (group as Record<string, any>)[name]) {
        zh = (group as Record<string, any>)[name].zh
        break
      }
    }
  }

  return zh || name
}
