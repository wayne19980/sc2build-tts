import { ref } from 'vue'
import type { CatalogItem } from '../data/catalog'

const stored = typeof localStorage !== 'undefined' ? localStorage.getItem('sc2-language') : null
const english = ref(stored === 'en')

export function useLanguage() {
  function displayName(item: CatalogItem | null | undefined, fallback = ''): string {
    if (!item) return fallback
    return english.value ? item.name : item.nameZh
  }

  function toggleLanguage(): void {
    english.value = !english.value
    localStorage.setItem('sc2-language', english.value ? 'en' : 'zh')
  }

  return { english, displayName, toggleLanguage }
}
