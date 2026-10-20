<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar-brand">
        <span class="brand-mark">SC2</span>
        <span>Build Lab</span>
        <span class="version">v{{ version }}</span>
      </div>
      <span class="tagline">本地赛事流程与科技树分析</span>
    </header>

    <div class="app-body">
      <AnalysisView />
    </div>
  </div>
</template>

<script setup lang="ts">
import packageInfo from '../package.json'
import AnalysisView from './components/analysis/AnalysisView.vue'

const version = packageInfo.version
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

.tagline {
  color: #5f7d9f;
  font-size: 10px;
  letter-spacing: 0.08em;
}

.app-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
