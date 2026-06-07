<template>
  <div
    v-tooltip.bottom="tooltipText"
    class="context-usage-ring"
    :class="severityClass"
    role="img"
    :aria-label="tooltipText"
  >
    <svg viewBox="0 0 36 36" class="context-usage-svg" aria-hidden="true">
      <circle class="context-usage-track" cx="18" cy="18" :r="radius" />
      <circle
        class="context-usage-progress"
        cx="18"
        cy="18"
        :r="radius"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="dashOffset"
      />
    </svg>
    <span class="context-usage-label">{{ displayPercent }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatTokenCount } from '../utils/contextUsage'

const props = defineProps({
  percentUsed: {
    type: Number,
    default: 0
  },
  promptTokens: {
    type: Number,
    default: 0
  },
  contextTokenLimit: {
    type: Number,
    default: 0
  },
  trimmedCount: {
    type: Number,
    default: 0
  },
  maxHistoryMessages: {
    type: Number,
    default: 0
  },
  model: {
    type: String,
    default: ''
  }
})

const radius = 14.5
const circumference = 2 * Math.PI * radius

const clampedPercent = computed(() => Math.max(0, Math.min(100, props.percentUsed || 0)))

const dashOffset = computed(() => circumference * (1 - clampedPercent.value / 100))

const displayPercent = computed(() => `${Math.round(clampedPercent.value)}`)

const severityClass = computed(() => {
  if (clampedPercent.value >= 90) return 'context-usage-ring--critical'
  if (clampedPercent.value >= 70) return 'context-usage-ring--warn'
  return 'context-usage-ring--ok'
})

const tooltipText = computed(() => {
  const modelLine = props.model ? `\nModel: ${props.model}` : ''
  const trimmedLine =
    props.trimmedCount > 0
      ? `\n${props.trimmedCount} older message(s) are trimmed before each send.`
      : props.maxHistoryMessages > 0
        ? `\nKeeps the last ${props.maxHistoryMessages} messages for this model.`
        : ''
  return [
    `Context ~${Math.round(clampedPercent.value)}% (estimated)`,
    `${formatTokenCount(props.promptTokens)} / ${formatTokenCount(props.contextTokenLimit)} tokens`,
    'Start a new chat if replies lose focus or hit limits.',
    trimmedLine,
    modelLine
  ]
    .filter(Boolean)
    .join('\n')
})
</script>

<style scoped>
.context-usage-ring {
  position: relative;
  width: 1.85rem;
  height: 1.85rem;
  flex-shrink: 0;
}

.context-usage-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.context-usage-track {
  fill: none;
  stroke: color-mix(in srgb, var(--p-text-muted-color) 22%, transparent);
  stroke-width: 3;
}

.context-usage-progress {
  fill: none;
  stroke: var(--context-ring-color, var(--p-primary-color));
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.25s ease, stroke 0.2s ease;
}

.context-usage-label {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--p-text-color);
  pointer-events: none;
}

.context-usage-ring--ok {
  --context-ring-color: var(--p-green-500);
}

.context-usage-ring--warn {
  --context-ring-color: var(--p-orange-500);
}

.context-usage-ring--critical {
  --context-ring-color: var(--p-red-500);
}
</style>
