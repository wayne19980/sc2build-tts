<template>
  <span v-if="supply" class="supply-breakdown">
    <span class="supply-total" :title="totalTitle">
      <span class="num">{{ supply.used }}</span>/<span class="num">{{ supply.made }}</span>
    </span>
    <span class="supply-part" :title="workerTitle">
      <span class="tag">{{ english ? 'W' : '农' }}</span>
      <span class="num">{{ supply.workers }}</span>
    </span>
    <span class="supply-part" :title="armyTitle">
      <span class="tag">{{ english ? 'A' : '兵' }}</span>
      <span class="num">{{ supply.army }}</span>
    </span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SupplyInfo } from '../../types-analysis'
import { useLanguage } from '../../composables/useLanguage'

const props = defineProps<{ supply?: SupplyInfo }>()
const { english } = useLanguage()

const totalTitle = computed(() =>
  english.value
    ? `Supply ${props.supply?.used ?? 0}/${props.supply?.made ?? 0}`
    : `人口 ${props.supply?.used ?? 0}/${props.supply?.made ?? 0}`,
)
const workerTitle = computed(() => (english.value ? 'Worker supply' : '农民人口'))
const armyTitle = computed(() => (english.value ? 'Army supply' : '部队人口'))
</script>

<style scoped>
.supply-breakdown {
  display: inline-flex;
  flex: none;
  align-items: center;
  gap: 5px;
  color: #8fb8e8;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 11px;
  line-height: 1;
}

.supply-total {
  display: inline-flex;
  align-items: baseline;
  padding: 1px 5px;
  border-radius: 4px;
  background: #102540;
  white-space: nowrap;
}

.supply-total .num:first-child {
  display: inline-block;
  min-width: 3ch;
  text-align: right;
}

.supply-total .num:last-child {
  display: inline-block;
  min-width: 3ch;
  text-align: left;
}

.supply-part {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  color: #7f9cbf;
}

.supply-part .tag {
  color: #5f7fa4;
  font-size: 10px;
}

.supply-part .num {
  display: inline-block;
  min-width: 3ch;
  text-align: right;
  color: #a9c8ea;
}
</style>
