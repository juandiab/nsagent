<template>
  <div class="flex justify-content-center">
    <img
      :src="logoSrc"
      alt="JPilot"
      class="jpilot-logo"
      :style="{ width: sizePx, height: sizePx }"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import logoLight from '../assets/JPilot-logo-big.svg'
import logoDark from '../assets/JPilot-logo-big-black.svg'
import { getTheme } from '../services/theme'

const props = defineProps({
  size: { type: [Number, String], default: 52 }
})

const theme = ref(getTheme())

const logoSrc = computed(() => (theme.value === 'dark' ? logoDark : logoLight))

const sizePx = computed(() =>
  typeof props.size === 'number' ? `${props.size}px` : props.size
)

function onThemeChange(event) {
  theme.value = event.detail
}

onMounted(() => {
  window.addEventListener('jpilot-theme-change', onThemeChange)
})

onUnmounted(() => {
  window.removeEventListener('jpilot-theme-change', onThemeChange)
})
</script>

<style scoped>
.jpilot-logo {
  display: block;
}
</style>
