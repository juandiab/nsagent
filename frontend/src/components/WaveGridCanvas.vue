<template>
  <canvas ref="canvasRef" class="wave-grid-canvas" aria-hidden="true" />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { bindCanvasResize } from '../utils/canvasResize'
import { onThemeChange, prefersReducedMotion, resolveCanvasColors } from '../utils/canvasTheme'

const props = defineProps({
  lineColor: { type: String, default: '' },
  lineOpacity: { type: Number, default: null }
})

const canvasRef = ref(null)
let animationId = null
let resizeCleanup = null
let themeCleanup = null
let tick = 0

function themeColors() {
  if (props.lineColor) {
    return { line: props.lineColor, opacity: props.lineOpacity ?? 0.3 }
  }
  return resolveCanvasColors(
    { line: '0,123,167', opacity: 0.14 },
    { line: '100,180,210', opacity: 0.12 }
  )
}

function resizeCanvas(canvas) {
  canvas.width = canvas.offsetWidth
  canvas.height = canvas.offsetHeight
}

function drawFrame(canvas, ctx, animate = true) {
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  const { line, opacity } = themeColors()
  const spacing = 36
  const time = animate ? tick * 0.018 : 0

  for (let y = spacing; y < canvas.height; y += spacing) {
    ctx.beginPath()
    for (let x = 0; x <= canvas.width; x += 4) {
      const wave = Math.sin(x * 0.012 + time + y * 0.04) * 10
      if (x === 0) ctx.moveTo(x, y + wave)
      else ctx.lineTo(x, y + wave)
    }
    const fade = 1 - Math.abs(y / canvas.height - 0.5) * 0.55
    ctx.strokeStyle = `rgba(${line}, ${opacity * fade})`
    ctx.lineWidth = props.lineColor ? 1.1 : 0.75
    ctx.stroke()
  }
}

function startAnimation() {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  const reducedMotion = prefersReducedMotion()
  let loopStarted = false

  const syncSize = () => {
    if (canvas.offsetWidth === 0 || canvas.offsetHeight === 0) return false
    resizeCanvas(canvas)
    return true
  }

  const ensureRunning = () => {
    if (!syncSize()) return
    if (reducedMotion) {
      drawFrame(canvas, ctx, false)
      return
    }
    if (loopStarted) return
    loopStarted = true
    const loop = () => {
      tick += 1
      drawFrame(canvas, ctx, true)
      animationId = requestAnimationFrame(loop)
    }
    loop()
  }

  resizeCleanup = bindCanvasResize(canvas, ensureRunning)
  themeCleanup = onThemeChange(() => {
    if (syncSize()) drawFrame(canvas, ctx, false)
  })
  ensureRunning()
}

onMounted(() => startAnimation())

onBeforeUnmount(() => {
  if (animationId) cancelAnimationFrame(animationId)
  resizeCleanup?.()
  themeCleanup?.()
})
</script>

<style scoped>
.wave-grid-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
