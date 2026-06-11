<template>
  <canvas
    ref="canvasRef"
    class="constellation-canvas"
    aria-hidden="true"
  />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  particleCount: { type: Number, default: 80 },
  linkDistance: { type: Number, default: 150 },
  lineColor: { type: String, default: '0,123,167' },
  dotColor: { type: String, default: '0,168,224' },
  lineOpacity: { type: Number, default: 0.25 },
  dotOpacity: { type: Number, default: 0.7 }
})

const canvasRef = ref(null)
let animationId = null
let resizeHandler = null
let particles = []

function resizeCanvas(canvas) {
  canvas.width = canvas.offsetWidth
  canvas.height = canvas.offsetHeight
}

function createParticles(canvas) {
  return Array.from({ length: props.particleCount }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.4,
    vy: (Math.random() - 0.5) * 0.4,
    r: Math.random() * 2 + 1
  }))
}

function drawFrame(canvas, ctx, animate = true) {
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const width = canvas.width
  const height = canvas.height

  if (animate) {
    particles.forEach((particle) => {
      particle.x += particle.vx
      particle.y += particle.vy

      if (particle.x < 0 || particle.x > width) {
        particle.vx *= -1
      }
      if (particle.y < 0 || particle.y > height) {
        particle.vy *= -1
      }
    })
  }

  for (let i = 0; i < particles.length; i += 1) {
    for (let j = i + 1; j < particles.length; j += 1) {
      const dx = particles[i].x - particles[j].x
      const dy = particles[i].y - particles[j].y
      const distance = Math.sqrt(dx * dx + dy * dy)

      if (distance < props.linkDistance) {
        const alpha = (1 - distance / props.linkDistance) * props.lineOpacity
        ctx.strokeStyle = `rgba(${props.lineColor}, ${alpha})`
        ctx.lineWidth = 0.8
        ctx.beginPath()
        ctx.moveTo(particles[i].x, particles[i].y)
        ctx.lineTo(particles[j].x, particles[j].y)
        ctx.stroke()
      }
    }
  }

  particles.forEach((particle) => {
    ctx.beginPath()
    ctx.arc(particle.x, particle.y, particle.r, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${props.dotColor}, ${props.dotOpacity})`
    ctx.fill()
  })
}

function startAnimation() {
  const canvas = canvasRef.value
  if (!canvas) {
    return
  }

  const ctx = canvas.getContext('2d')
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  resizeCanvas(canvas)
  particles = createParticles(canvas)

  resizeHandler = () => {
    resizeCanvas(canvas)
    particles = createParticles(canvas)
    if (reducedMotion) {
      drawFrame(canvas, ctx, false)
    }
  }

  window.addEventListener('resize', resizeHandler, { passive: true })

  if (reducedMotion) {
    drawFrame(canvas, ctx, false)
    return
  }

  const tick = () => {
    drawFrame(canvas, ctx, true)
    animationId = requestAnimationFrame(tick)
  }

  tick()
}

onMounted(() => {
  startAnimation()
})

onBeforeUnmount(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
  }
})
</script>

<style scoped>
.constellation-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
