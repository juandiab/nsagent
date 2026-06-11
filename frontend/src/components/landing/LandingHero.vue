<template>
  <section class="landing-hero">
    <div class="landing-hero-bg" aria-hidden="true">
      <ConstellationCanvas
        line-color="52,211,153"
        dot-color="16,185,129"
        :line-opacity="0.22"
        :dot-opacity="0.65"
      />
    </div>

    <div class="landing-container landing-hero-inner">
      <LandingNavbar />

      <div class="landing-hero-grid">
        <div class="landing-hero-copy landing-fade-in">
          <img src="/jpilot-favicon.png" alt="JPilot" class="landing-hero-logo" width="72" height="72" />
          <span class="landing-hero-tag">AI-assisted appliance management</span>
          <h1 class="landing-hero-title">
            Operate NetScaler, Cisco, and F5 with confidence
          </h1>
          <p class="landing-hero-lead">
            JPilot connects your appliance inventory to your own AI provider keys — so your team can plan,
            configure, and troubleshoot with vendor-aware tools, not generic chat.
          </p>
          <div class="landing-hero-actions landing-fade-in landing-fade-in-delay-1">
            <RouterLink to="/login" class="landing-btn landing-btn-primary">Get access</RouterLink>
            <a href="#install" class="landing-btn landing-btn-outline">Install JPilot</a>
          </div>
          <div class="landing-hero-stats landing-fade-in landing-fade-in-delay-2">
            <div v-for="stat in stats" :key="stat.label" class="landing-hero-stat">
              <span class="landing-hero-stat-value">{{ stat.value }}</span>
              <span class="landing-hero-stat-label">{{ stat.label }}</span>
            </div>
          </div>
        </div>

        <div class="landing-hero-visual landing-fade-in landing-fade-in-delay-2" aria-hidden="true">
          <img :src="heroImg1" alt="" class="landing-hero-shot landing-hero-shot-main" />
          <img :src="heroImg2" alt="" class="landing-hero-shot landing-hero-shot-overlay" />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import heroImg1 from '../../assets/landing/hero-img-1.png'
import heroImg2 from '../../assets/landing/hero-img-2.png'
import ConstellationCanvas from '../ConstellationCanvas.vue'
import LandingNavbar from './LandingNavbar.vue'

const stats = [
  { value: '4', label: 'Vendor platforms' },
  { value: 'BYOK', label: 'Your AI keys' },
  { value: 'MCP', label: 'Tool-calling agent' }
]
</script>

<style scoped>
.landing-hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, var(--landing-hero-from) 0%, var(--landing-hero-to) 100%);
  color: var(--landing-text-on-hero);
}

.landing-hero-bg {
  position: absolute;
  inset: 0;
  opacity: 0.55;
  pointer-events: none;
}

.landing-hero-inner {
  position: relative;
  z-index: 1;
  padding-bottom: 4rem;
}

.landing-hero-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2.5rem;
  align-items: center;
  margin-top: 2.5rem;
}

.landing-hero-logo {
  display: block;
  width: 4.5rem;
  height: 4.5rem;
  margin-bottom: 0.75rem;
  border-radius: 50%;
  object-fit: cover;
  filter: drop-shadow(0 8px 24px rgba(0, 0, 0, 0.35));
}

.landing-hero-tag {
  display: inline-flex;
  margin-bottom: 1rem;
  padding: 0.3rem 0.75rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.06);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--landing-primary);
}

.landing-hero-lead {
  margin: 1.25rem 0 0;
  max-width: 34rem;
  font-size: 1.0625rem;
  line-height: 1.65;
  color: var(--landing-text-muted-on-hero);
}

.landing-hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-top: 1.75rem;
}

.landing-hero-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin-top: 2.5rem;
  max-width: 28rem;
}

.landing-hero-stat {
  padding: 0.875rem 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
}

.landing-hero-stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: #fff;
}

.landing-hero-stat-label {
  display: block;
  margin-top: 0.2rem;
  font-size: 0.75rem;
  color: var(--landing-text-muted-on-hero);
}

.landing-hero-visual {
  position: relative;
  min-height: 18rem;
}

.landing-hero-shot {
  border-radius: 1rem;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.28);
}

.landing-hero-shot-main {
  width: min(100%, 22rem);
  margin-inline: auto;
  display: block;
}

.landing-hero-shot-overlay {
  position: absolute;
  width: min(72%, 16rem);
  right: 8%;
  bottom: -1.5rem;
}

@media (min-width: 960px) {
  .landing-hero-grid {
    grid-template-columns: 1.05fr 0.95fr;
    gap: 3rem;
    margin-top: 4rem;
  }

  .landing-hero-shot-main {
    margin-inline: 0 0 auto;
  }

  .landing-hero-shot-overlay {
    right: 0;
    bottom: 2rem;
  }
}
</style>
