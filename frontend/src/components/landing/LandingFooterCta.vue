<template>
  <section class="landing-section-tight landing-footer-cta">
    <div class="landing-container">
      <div class="landing-gradient-panel landing-footer-panel">
        <h2 class="landing-footer-title">Ready to manage your appliances with JPilot?</h2>
        <p class="landing-footer-lead">
          Sign in to your platform or install JPilot locally. The Free edition lets your team explore the product
          with your own AI provider keys.
        </p>
        <div class="landing-footer-actions">
          <RouterLink to="/login" class="landing-btn landing-btn-primary">Get access</RouterLink>
          <a href="#install" class="landing-btn landing-btn-outline">View install steps</a>
        </div>
      </div>

      <p class="landing-disclaimer">
        JPilot is an independent product by Nexxus-Tech SAS. It is not affiliated with, endorsed by, sponsored by,
        or certified by Cloud Software Group (Citrix / NetScaler), Cisco Systems, F5 Networks, or their affiliates.
        NetScaler, Citrix, Cisco, F5 BIG-IP, and related names are trademarks of their respective owners and are
        used here only for identification and interoperability.
      </p>

      <footer class="landing-footer-meta">
        <div class="landing-footer-brand">
          <img src="/jpilot-favicon.png" alt="JPilot" class="landing-footer-logo" />
          <span>JPilot by Nexxus-Tech SAS</span>
        </div>
        <div class="landing-footer-links">
          <RouterLink to="/legal/terms-of-service">Terms</RouterLink>
          <RouterLink to="/legal/privacy-policy">Privacy</RouterLink>
          <RouterLink to="/plans">Plans</RouterLink>
          <a href="https://www.nexxus-tech.com" target="_blank" rel="noopener noreferrer">Nexxus Tech</a>
        </div>
      </footer>
    </div>
  </section>
</template>

<script setup>
</script>

<style scoped>
.landing-footer-panel {
  padding: 3rem 1.5rem;
  text-align: center;
}

.landing-footer-title {
  margin: 0;
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 700;
  line-height: 1.1;
  color: #fff;
}

.landing-footer-lead {
  margin: 1rem auto 0;
  max-width: 34rem;
  color: var(--landing-text-muted-on-hero);
  line-height: 1.65;
}

.landing-footer-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
  margin-top: 1.75rem;
}

.landing-disclaimer {
  margin: 2rem auto 0;
  max-width: 42rem;
  text-align: center;
  font-size: 0.78rem;
  line-height: 1.65;
  color: var(--landing-text-muted);
}

.landing-footer-meta {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: center;
  justify-content: space-between;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--landing-border);
  color: var(--landing-text-muted);
  font-size: 0.875rem;
}

.landing-footer-brand {
  display: inline-flex;
  align-items: center;
  gap: 0.625rem;
}

.landing-footer-logo {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  object-fit: cover;
}

.landing-footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: center;
}

.landing-footer-links a {
  color: var(--landing-text-muted);
  text-decoration: none;
}

.landing-footer-links a:hover {
  color: var(--p-primary-color);
}

@media (min-width: 768px) {
  .landing-footer-panel {
    padding: 4rem 2.5rem;
  }

  .landing-footer-meta {
    flex-direction: row;
  }
}
</style>
