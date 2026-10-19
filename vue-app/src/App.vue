<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar-brand">
        <span class="brand-mark">SC2</span>
        <span>Build Lab</span>
      </div>
      <nav class="topbar-nav">
        <button :class="{ active: view === 'analysis' }" @click="view = 'analysis'">
          科技树分析
        </button>
        <button :class="{ active: view === 'legacy' }" @click="view = 'legacy'">
          旧版播报
        </button>
      </nav>
    </header>

    <div class="app-body" :class="{ legacy: view === 'legacy' }">
      <AnalysisView v-if="view === 'analysis'" />
      <LegacyApp v-else />
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent, ref } from 'vue'
import AnalysisView from './components/analysis/AnalysisView.vue'

const LegacyApp = defineAsyncComponent(() => import('./LegacyApp.vue'))
const view = ref<'analysis' | 'legacy'>('analysis')
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

.topbar-nav {
  display: flex;
  gap: 4px;
}

.topbar-nav button {
  padding: 6px 12px;
  border: 1px solid transparent;
  border-radius: 7px;
  background: transparent;
  color: #7893b5;
  font-size: 12px;
  cursor: pointer;
}

.topbar-nav button:hover {
  color: #cfe3fa;
  background: #0d1929;
}

.topbar-nav button.active {
  color: #e8f3ff;
  border-color: #2f6caf;
  background: #0e1d30;
}

.app-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.app-body.legacy {
  overflow: auto;
}
</style>
