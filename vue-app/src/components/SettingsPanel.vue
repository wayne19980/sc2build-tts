<template>
  <div class="settings-backdrop" @click.self="emit('close')">
    <section class="settings-panel" role="dialog" aria-modal="true" aria-labelledby="settings-title">
      <header class="settings-head">
        <div>
          <div class="settings-eyebrow">Settings</div>
          <h2 id="settings-title">设置</h2>
        </div>
        <button class="settings-close" title="关闭" @click="emit('close')">×</button>
      </header>

      <div class="settings-body">
        <section class="settings-section">
          <h3>录像库</h3>
          <label class="setting-row">
            <span class="setting-copy">
              <span class="setting-title">显示农民数量</span>
              <span class="setting-hint">在兵种预览中包含 Probe / SCV / Drone</span>
            </span>
            <input v-model="settings.showLibraryWorkers" type="checkbox" />
          </label>
        </section>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { useSettings } from '../composables/useSettings'

const emit = defineEmits<{
  (event: 'close'): void
}>()

const { settings } = useSettings()

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
}

onMounted(() => window.addEventListener('keydown', handleKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', handleKeydown))
</script>

<style scoped>
.settings-backdrop {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(2, 5, 11, 0.68);
  backdrop-filter: blur(3px);
}

.settings-panel {
  width: min(520px, 100%);
  max-height: min(640px, 90vh);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #1d3352;
  border-radius: 12px;
  background: linear-gradient(180deg, #0c1728, #070d18);
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.6);
}

.settings-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid #142238;
}

.settings-eyebrow {
  color: #5f7d9f;
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.settings-head h2 {
  margin: 3px 0 0;
  color: #e8f4ff;
  font-size: 20px;
  font-weight: 700;
}

.settings-close {
  width: 28px;
  height: 28px;
  padding: 0;
  border: 1px solid #1d3352;
  border-radius: 6px;
  background: #080f1c;
  color: #9fb8d8;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}

.settings-close:hover {
  border-color: #3d7fc4;
  color: #eaf4ff;
}

.settings-body {
  overflow: auto;
  padding: 16px 20px 20px;
  scrollbar-width: thin;
  scrollbar-color: #31527a transparent;
}

.settings-section + .settings-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #142238;
}

.settings-section h3 {
  margin: 0 0 10px;
  color: #7ca5cf;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 10px 12px;
  border: 1px solid #162a45;
  border-radius: 8px;
  background: rgba(9, 17, 30, 0.7);
  cursor: pointer;
}

.setting-row:hover {
  border-color: #24466f;
}

.setting-copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.setting-title {
  color: #d8eaff;
  font-size: 13px;
  font-weight: 600;
}

.setting-hint {
  color: #6f89ad;
  font-size: 11px;
  line-height: 1.3;
}

.setting-row input[type='checkbox'] {
  position: relative;
  flex: none;
  width: 38px;
  height: 21px;
  margin: 0;
  border: 1px solid #2a4768;
  border-radius: 999px;
  appearance: none;
  background: #101d30;
  cursor: pointer;
  transition: background 160ms ease, border-color 160ms ease;
}

.setting-row input[type='checkbox']::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  background: #7896b9;
  transition: transform 160ms ease, background 160ms ease;
}

.setting-row input[type='checkbox']:checked {
  border-color: #3d7fc4;
  background: #245a94;
}

.setting-row input[type='checkbox']:checked::after {
  transform: translateX(17px);
  background: #eaf4ff;
}
</style>
