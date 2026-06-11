<template>
  <div class="landing-page">
    <LandingHero />
    <LandingFeatures />
    <LandingSolutions />
    <LandingInstall />
    <LandingFooterCta />
  </div>
</template>

<script setup>
import LandingFeatures from '../components/landing/LandingFeatures.vue'
import LandingFooterCta from '../components/landing/LandingFooterCta.vue'
import LandingHero from '../components/landing/LandingHero.vue'
import LandingInstall from '../components/landing/LandingInstall.vue'
import LandingSolutions from '../components/landing/LandingSolutions.vue'
import '../assets/styles/landing.css'
</script>
