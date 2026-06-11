<template>
  <section id="install" class="landing-section">
    <div class="landing-container landing-install">
      <div class="landing-install-head">
        <span class="landing-eyebrow">Get started</span>
        <h2 class="landing-title">Install JPilot in one command</h2>
        <p class="landing-lead">
          The installer downloads JPilot, generates secrets and TLS, launches the Docker stack, and opens the UI in your browser.
        </p>
      </div>

      <LandingInstallBlock />

      <p class="landing-install-note">
        Need help? Visit
        <a href="https://www.nexxus-tech.com" target="_blank" rel="noopener noreferrer">nexxus-tech.com</a>
        or email
        <a href="mailto:support@nexxus-tech.com">support@nexxus-tech.com</a>.
        Once the stack is running, finish setup in the browser and sign in.
      </p>
    </div>
  </section>
</template>

<script setup>
import LandingInstallBlock from './LandingInstallBlock.vue'
</script>

<style scoped>
.landing-install-head {
  max-width: 40rem;
  margin-inline: auto;
  text-align: center;
}

.landing-install-head .landing-title {
  margin-top: 0.75rem;
}

.landing-install-head .landing-lead {
  margin-top: 1rem;
}

.landing-install-note {
  margin: 1.75rem auto 0;
  max-width: 40rem;
  text-align: center;
  color: var(--landing-text-muted);
  line-height: 1.6;
  font-size: 0.9375rem;
}

.landing-install-note a {
  color: var(--p-primary-color);
  text-decoration: none;
}

.landing-install-note a:hover {
  text-decoration: underline;
}
</style>
