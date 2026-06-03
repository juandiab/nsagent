<template>
  <div class="usage-meter">
    <div class="usage-meter-head">
      <span class="usage-meter-label">{{ label }}</span>
      <span class="usage-meter-value">{{ summaryText }}</span>
    </div>
    <ProgressBar :value="barValue" :show-value="false" :class="barClass" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ProgressBar from 'primevue/progressbar'
import { formatCount } from '../services/modelUsage'

const props = defineProps({
  label: { type: String, required: true },
  used: { type: Number, default: 0 },
  limit: { type: Number, default: null },
  percent: { type: Number, default: null },
  remaining: { type: Number, default: null },
  unlimited: { type: Boolean, default: false },
  unit: { type: String, default: '' }
})

const barValue = computed(() => {
  if (props.percent != null) return Math.min(100, props.percent)
  if (props.unlimited || props.limit == null) return props.used > 0 ? 8 : 0
  return 0
})

const barClass = computed(() => {
  const p = props.percent
  if (p == null) return ''
  if (p >= 90) return 'usage-bar-danger'
  if (p >= 75) return 'usage-bar-warn'
  return 'usage-bar-ok'
})

const summaryText = computed(() => {
  const used = formatCount(props.used)
  if (props.unlimited || props.limit == null) {
    return `${used} ${props.unit} this month`
  }
  const limit = formatCount(props.limit)
  const left = formatCount(props.remaining ?? Math.max(0, (props.limit || 0) - props.used))
  return `${used} / ${limit} ${props.unit} · ${left} remaining`
})
</script>

<style scoped>
.usage-meter-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}

.usage-meter-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--p-text-muted-color);
}

.usage-meter-value {
  font-size: 0.7rem;
  color: var(--p-text-muted-color);
  text-align: right;
}

:deep(.p-progressbar) {
  height: 0.55rem;
  border-radius: 999px;
  background: var(--p-surface-200);
}

:deep(.usage-bar-ok .p-progressbar-value) {
  background: linear-gradient(90deg, #34d399, #10b981);
}

:deep(.usage-bar-warn .p-progressbar-value) {
  background: linear-gradient(90deg, #fbbf24, #f59e0b);
}

:deep(.usage-bar-danger .p-progressbar-value) {
  background: linear-gradient(90deg, #f87171, #ef4444);
}
</style>
