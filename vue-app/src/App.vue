<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar-brand">
        <span class="brand-mark">SC2</span>
        <span>Build Lab</span>
        <span class="version">v{{ version }}</span>
      </div>
      <div class="topbar-right">
        <span class="tagline">本地赛事流程与科技树分析</span>
        <button v-if="isDesktop" class="update-check" :disabled="checking" @click="checkForUpdates(true)">
          {{ checking ? '检查中…' : '检查更新' }}
        </button>
        <button class="lang-toggle" @click="toggleLanguage">{{ english ? 'EN' : '中' }}</button>
      </div>
    </header>

    <div class="app-body">
      <AnalysisView />
    </div>
    <UpdateBanner />
  </div>
</template>

<script setup lang="ts">
import packageInfo from '../package.json'
import AnalysisView from './components/analysis/AnalysisView.vue'
import { onMounted } from 'vue'
import { useLanguage } from './composables/useLanguage'
import { useUpdater } from './composables/useUpdater'
import { isTauriRuntime } from './composables/useTauri'
import UpdateBanner from './components/UpdateBanner.vue'

const version = packageInfo.version
const isDesktop = isTauriRuntime()
const { english, toggleLanguage } = useLanguage()
const { checking, checkForUpdates, autoCheck } = useUpdater()

onMounted(() => {
  void autoCheck()
})
</script>

<style>
* {
  box-sizing: border-box;
}

html,
body,
#app {
  height: 100%;
}

#app {
  width: 100%;
  max-width: none;
  margin: 0;
  text-align: left;
  border: 0;
  min-height: 100%;
  display: block;
}

body {
  margin: 0;
  background: #050811;
  color: #dce8f8;
  font-family: 'Noto Sans SC', 'Segoe UI', system-ui, sans-serif;
}

.app-shell {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #050811;
}

.topbar {
  flex: none;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid #142238;
  background: linear-gradient(180deg, #0b1526, #070d18);
}

.topbar-brand {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #dcecff;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.topbar-brand .brand-mark {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: linear-gradient(135deg, #2f7fe0, #7b5cff);
  color: #fff;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.06em;
  box-shadow: 0 0 18px rgba(60, 120, 255, 0.35);
}

.version {
  padding: 1px 5px;
  border: 1px solid #1d3352;
  border-radius: 4px;
  color: #6f89ad;
  font-size: 9px;
  font-weight: 500;
  letter-spacing: 0.04em;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tagline {
  color: #5f7d9f;
  font-size: 10px;
  letter-spacing: 0.08em;
}

.update-check {
  padding: 3px 8px;
  border: 1px solid #1d3352;
  border-radius: 5px;
  background: transparent;
  color: #8ca6c8;
  font-size: 10px;
  cursor: pointer;
}

.update-check:hover {
  border-color: #3d7fc4;
  color: #e8f4ff;
}

.update-check:disabled {
  opacity: 0.5;
  cursor: default;
}

.lang-toggle {
  padding: 3px 8px;
  border: 1px solid #1d3352;
  border-radius: 5px;
  background: #080f1c;
  color: #9fb8d8;
  font-size: 10px;
  font-weight: 700;
  cursor: pointer;
}

.lang-toggle:hover {
  border-color: #3d7fc4;
  color: #e8f4ff;
}

.app-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
