<template>
  <canvas ref="canvasRef" class="drift-field-canvas" aria-hidden="true" />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { bindCanvasResize } from '../utils/canvasResize'
import { onThemeChange, prefersReducedMotion, resolveCanvasColors } from '../utils/canvasTheme'

const props = defineProps({
  dotColor: { type: String, default: '' },
  dotOpacity: { type: Number, default: null }
})

const canvasRef = ref(null)
let animationId = null
let resizeCleanup = null
let themeCleanup = null
let particles = []

function themeColors() {
  if (props.dotColor) {
    return { dot: props.dotColor, opacity: props.dotOpacity ?? 0.5 }
  }
  return resolveCanvasColors(
    { dot: '0,123,167', opacity: 0.35 },
    { dot: '0,168,224', opacity: 0.28 }
  )
}

function resizeCanvas(canvas) {
  canvas.width = canvas.offsetWidth
  canvas.height = canvas.offsetHeight
}

function createParticles(canvas) {
  const count = Math.min(60, Math.floor((canvas.width * canvas.height) / 12000))
  return Array.from({ length: Math.max(count, 24) }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.25,
    vy: (Math.random() - 0.5) * 0.25,
    r: Math.random() * 1.8 + 0.6,
    phase: Math.random() * Math.PI * 2
  }))
}

function drawFrame(canvas, ctx, animate = true) {
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  const { dot, opacity } = themeColors()

  if (animate) {
    particles.forEach((p) => {
      p.x += p.vx
      p.y += p.vy
      p.phase += 0.012
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1
    })
  }

  const glow = Boolean(props.dotColor)

  particles.forEach((p) => {
    const pulse = 0.65 + Math.sin(p.phase) * 0.35
    const radius = p.r * pulse * (glow ? 1.15 : 1)
    if (glow) {
      ctx.beginPath()
      ctx.arc(p.x, p.y, radius * 2.2, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${dot}, ${opacity * pulse * 0.22})`
      ctx.fill()
    }
    ctx.beginPath()
    ctx.arc(p.x, p.y, radius, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${dot}, ${opacity * pulse})`
    ctx.fill()
  })
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
    particles = createParticles(canvas)
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
    const tick = () => {
      drawFrame(canvas, ctx, true)
      animationId = requestAnimationFrame(tick)
    }
    tick()
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
.drift-field-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
