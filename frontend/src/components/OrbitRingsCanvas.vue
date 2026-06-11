<template>
  <canvas ref="canvasRef" class="orbit-rings-canvas" aria-hidden="true" />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { bindCanvasResize } from '../utils/canvasResize'
import { onThemeChange, prefersReducedMotion, resolveCanvasColors } from '../utils/canvasTheme'

const props = defineProps({
  ringColor: { type: String, default: '' },
  dotColor: { type: String, default: '' },
  ringOpacity: { type: Number, default: null },
  dotOpacity: { type: Number, default: null }
})

const canvasRef = ref(null)
let animationId = null
let resizeCleanup = null
let themeCleanup = null
let angle = 0

function themeColors() {
  if (props.ringColor) {
    return {
      ring: props.ringColor,
      dot: props.dotColor || props.ringColor,
      ringOpacity: props.ringOpacity ?? 0.5,
      dotOpacity: props.dotOpacity ?? 0.8
    }
  }
  return resolveCanvasColors(
    { ring: '0,123,167', dot: '0,168,224', ringOpacity: 0.16, dotOpacity: 0.5 },
    { ring: '80,160,200', dot: '120,200,230', ringOpacity: 0.14, dotOpacity: 0.42 }
  )
}

function resizeCanvas(canvas) {
  canvas.width = canvas.offsetWidth
  canvas.height = canvas.offsetHeight
}

function drawFrame(canvas, ctx, animate = true) {
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  const colors = themeColors()
  const cx = canvas.width * 0.62
  const cy = canvas.height * 0.48
  const base = Math.min(canvas.width, canvas.height) * 0.22

  if (animate) angle += 0.003

  for (let i = 0; i < 4; i += 1) {
    const radius = base + i * base * 0.55
    const ringAngle = angle * (i % 2 === 0 ? 1 : -0.7) + i * 0.4

    ctx.beginPath()
    ctx.arc(cx, cy, radius, 0, Math.PI * 2)
    ctx.strokeStyle = `rgba(${colors.ring}, ${colors.ringOpacity * (1 - i * 0.15)})`
    ctx.lineWidth = props.ringColor ? 1.25 : 0.9
    ctx.stroke()

    const dotX = cx + Math.cos(ringAngle) * radius
    const dotY = cy + Math.sin(ringAngle) * radius
    ctx.beginPath()
    ctx.arc(dotX, dotY, 2.2 - i * 0.2, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${colors.dot}, ${colors.dotOpacity})`
    ctx.fill()
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
.orbit-rings-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
