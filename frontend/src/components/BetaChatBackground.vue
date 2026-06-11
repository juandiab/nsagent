<template>
  <div
    class="beta-chat-bg"
    :class="`beta-chat-bg--${base}`"
    aria-hidden="true"
  >
    <div class="beta-chat-bg-base" />
    <ConstellationCanvas
      v-if="backgroundId === 'constellation'"
      :particle-count="preview ? 28 : 72"
      :link-distance="preview ? 90 : 150"
      :line-color="constellationPalette.line"
      :dot-color="constellationPalette.dot"
      :line-opacity="constellationPalette.lineOpacity"
      :dot-opacity="constellationPalette.dotOpacity"
    />
    <DriftFieldCanvas
      v-else-if="backgroundId === 'drift'"
      :dot-color="driftPalette.dot"
      :dot-opacity="driftPalette.opacity"
    />
    <WaveGridCanvas
      v-else-if="backgroundId === 'waves'"
      :line-color="wavesPalette.line"
      :line-opacity="wavesPalette.opacity"
    />
    <OrbitRingsCanvas
      v-else-if="backgroundId === 'orbit'"
      :ring-color="orbitPalette.ring"
      :dot-color="orbitPalette.dot"
      :ring-opacity="orbitPalette.ringOpacity"
      :dot-opacity="orbitPalette.dotOpacity"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ConstellationCanvas from './ConstellationCanvas.vue'
import DriftFieldCanvas from './DriftFieldCanvas.vue'
import OrbitRingsCanvas from './OrbitRingsCanvas.vue'
import WaveGridCanvas from './WaveGridCanvas.vue'
import {
  BETA_BACKGROUND_PALETTES,
  getBetaBackgroundBase
} from '../utils/betaBackgroundPalettes'

const props = defineProps({
  backgroundId: { type: String, default: 'constellation' },
  preview: { type: Boolean, default: false }
})

const base = computed(() => getBetaBackgroundBase(props.backgroundId))

const constellationPalette = computed(() => BETA_BACKGROUND_PALETTES.constellation)
const driftPalette = computed(() => BETA_BACKGROUND_PALETTES.drift)
const wavesPalette = computed(() => BETA_BACKGROUND_PALETTES.waves)
const orbitPalette = computed(() => BETA_BACKGROUND_PALETTES.orbit)
</script>

<style scoped>
.beta-chat-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.beta-chat-bg-base {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.beta-chat-bg--white .beta-chat-bg-base {
  background: #ffffff;
}

.beta-chat-bg--black .beta-chat-bg-base {
  background: #000000;
}

.beta-chat-bg :deep(canvas) {
  position: absolute;
  inset: 0;
  z-index: 1;
  width: 100%;
  height: 100%;
}
</style>
