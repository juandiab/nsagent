<template>
  <div class="page">
    <PageHeader
      title="Plans"
      subtitle="Free core platform · Enterprise add-ons from Nexxus Tech"
    />

    <div class="hero-banner content-panel content-panel-padded mb-5">
      <p class="hero-eyebrow m-0">JPilot by Nexxus Tech</p>
      <h2 class="hero-title m-0 mt-2">Free, unlimited, on-premises</h2>
      <p class="hero-copy m-0 mt-3">
        The core platform is <strong>free</strong> — unlimited NetScalers and LLM providers, deployed
        <strong>on-prem</strong> with Docker. Credentials and config stay in your network. Encrypted
        secrets, JWT sessions, optional passkeys, and containers you can monitor with your own tooling.
      </p>
    </div>

    <div class="grid highlights-grid mb-5">
      <div
        v-for="item in PLATFORM_HIGHLIGHTS"
        :key="item.title"
        class="col-12 sm:col-6 lg:col-4"
      >
        <div class="highlight-card h-full">
          <i :class="['highlight-icon', item.icon]" />
          <h3 class="highlight-title">{{ item.title }}</h3>
          <p class="highlight-copy m-0">{{ item.description }}</p>
        </div>
      </div>
    </div>

    <div class="grid plan-grid">
      <div
        v-for="plan in PRICING_PLANS"
        :key="plan.id"
        class="col-12 lg:col-4"
      >
        <div
          class="plan-card h-full flex flex-column"
          :class="[
            `plan-card-${plan.id}`,
            {
              'plan-card-featured': plan.highlighted,
              'plan-card-interactive': plan.ctaHref
            }
          ]"
        >
          <div class="plan-card-header">
            <div class="flex align-items-start justify-content-between gap-2">
              <div>
                <h3 class="plan-name m-0">{{ plan.name }}</h3>
                <p class="plan-tagline m-0 mt-1">{{ plan.tagline }}</p>
              </div>
              <Tag
                v-if="plan.highlighted"
                value="Current"
                severity="success"
              />
            </div>

            <div v-if="plan.priceLabel" class="plan-price mt-4">
              <span class="plan-price-value">{{ plan.priceLabel }}</span>
              <span class="plan-price-detail">{{ plan.priceDetail }}</span>
            </div>
            <p v-else class="plan-price-substitute m-0 mt-4">{{ plan.priceDetail }}</p>
          </div>

          <ul class="plan-features flex-1 m-0 p-0 list-none">
            <li v-for="feature in plan.features" :key="feature">
              <i class="pi pi-check" />
              <span>{{ feature }}</span>
            </li>
          </ul>

          <div class="plan-cta mt-4">
            <Button
              v-if="plan.ctaHref"
              as="a"
              :href="plan.ctaHref"
              target="_blank"
              rel="noopener noreferrer"
              :label="plan.ctaLabel"
              icon="pi pi-envelope"
              icon-pos="right"
              severity="success"
              raised
              class="w-full contact-cta-btn"
            />
            <Button
              v-else
              :label="plan.ctaLabel"
              class="w-full"
              disabled
            />
          </div>
        </div>
      </div>
    </div>

    <div class="content-panel content-panel-padded contact-banner contact-banner-interactive mt-5">
      <div class="flex flex-column md:flex-row md:align-items-center md:justify-content-between gap-4">
        <div>
          <h3 class="panel-heading m-0">Need Enterprise?</h3>
          <p class="section-copy m-0 mt-2">
            Nexxus Tech can add SSO, custom runbooks, WAF/GSLB programs, engineer-led rollouts,
            migrations, health checks, and security enablements for F5, NetScaler, NGINX, and CVAD
            — on-premises, AWS, or Azure.
          </p>
        </div>
        <Button
          as="a"
          :href="NEXXUS_TECH.contactUrl"
          target="_blank"
          rel="noopener noreferrer"
          label="Contact us"
          icon="pi pi-arrow-up-right"
          icon-pos="right"
          severity="success"
          raised
          class="contact-banner-btn contact-cta-btn flex-shrink-0"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import PageHeader from '../components/PageHeader.vue'
import { NEXXUS_TECH } from '../config/nexxusTech'
import { PLATFORM_HIGHLIGHTS, PRICING_PLANS } from '../config/pricingPlans'
</script>

<style scoped>
.page {
  animation: page-in 0.35s ease;
}

.hero-eyebrow {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--p-primary-color);
}

.hero-title {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--p-text-color);
}

.hero-copy {
  font-size: 0.9375rem;
  line-height: 1.65;
  color: var(--p-text-muted-color);
  max-width: 52rem;
}

.hero-copy strong {
  color: var(--p-text-color);
  font-weight: 600;
}

.highlight-card {
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: var(--content-radius);
  padding: 1.25rem;
}

.highlight-icon {
  font-size: 1.25rem;
  color: var(--p-primary-color);
  margin-bottom: 0.75rem;
  display: block;
}

.highlight-title {
  margin: 0 0 0.35rem;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.highlight-copy {
  font-size: 0.8125rem;
  line-height: 1.55;
  color: var(--p-text-muted-color);
}

.plan-card {
  border: 1px solid var(--p-content-border-color);
  border-radius: var(--content-radius);
  padding: 1.5rem;
  transition:
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.28s ease;
  will-change: transform, box-shadow;
}

.plan-card-free {
  background: linear-gradient(
    160deg,
    #f8fafc 0%,
    #f0fdf4 55%,
    #ecfdf5 100%
  );
  border-color: #bbf7d0;
}

html.app-dark .plan-card-free {
  background: linear-gradient(
    160deg,
    #0f172a 0%,
    #14532d 45%,
    #052e16 100%
  );
  border-color: #166534;
}

.plan-card-enterprise {
  background: linear-gradient(
    160deg,
    #eff6ff 0%,
    #dbeafe 50%,
    #bfdbfe 100%
  );
  border-color: #60a5fa;
}

html.app-dark .plan-card-enterprise {
  background: linear-gradient(
    160deg,
    #0c1929 0%,
    #1e3a8a 50%,
    #172554 100%
  );
  border-color: #3b82f6;
}

.plan-card-enterprise-pro {
  background: linear-gradient(
    160deg,
    #faf5ff 0%,
    #ede9fe 45%,
    #ddd6fe 100%
  );
  border-color: #a78bfa;
}

html.app-dark .plan-card-enterprise-pro {
  background: linear-gradient(
    160deg,
    #1a0b2e 0%,
    #4c1d95 50%,
    #2e1065 100%
  );
  border-color: #8b5cf6;
}

.plan-card-enterprise .plan-features li i {
  color: #2563eb;
}

.plan-card-enterprise-pro .plan-features li i {
  color: #7c3aed;
}

.plan-card-free .plan-features li i {
  color: #16a34a;
}

html.app-dark .plan-card-enterprise .plan-features li i {
  color: #93c5fd;
}

html.app-dark .plan-card-enterprise-pro .plan-features li i {
  color: #c4b5fd;
}

html.app-dark .plan-card-free .plan-features li i {
  color: #86efac;
}

.plan-card-interactive {
  cursor: pointer;
  --contact-accent-bar: rgba(34, 197, 94, 0.35);
  --contact-accent-glow: rgba(34, 197, 94, 0.16);
}

html.app-dark .plan-card-interactive {
  --contact-accent-glow: rgba(74, 222, 128, 0.22);
  --contact-accent-bar: rgba(74, 222, 128, 0.4);
}

@media (hover: hover) {
  .plan-card-interactive:hover,
  .plan-card-interactive:focus-within {
    transform: translateY(-8px);
    box-shadow:
      0 4px 0 var(--contact-accent-bar),
      0 18px 36px var(--contact-accent-glow),
      0 8px 16px rgba(0, 0, 0, 0.08);
  }

  .plan-card-enterprise:hover,
  .plan-card-enterprise:focus-within {
    border-color: #2563eb;
  }

  .plan-card-enterprise-pro:hover,
  .plan-card-enterprise-pro:focus-within {
    border-color: #7c3aed;
  }
}

.plan-card-featured {
  border-color: var(--p-primary-200);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
}

html.app-dark .plan-card-featured {
  border-color: var(--p-primary-700);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.contact-cta-btn {
  transition:
    transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.22s cubic-bezier(0.22, 1, 0.36, 1),
    background 0.22s ease !important;
  background: linear-gradient(180deg, #34d399 0%, #22c55e 45%, #16a34a 100%) !important;
  border: 1px solid #15803d !important;
  color: #ffffff !important;
  box-shadow:
    0 4px 0 #14532d,
    0 8px 18px rgba(22, 163, 74, 0.35) !important;
}

.contact-cta-btn :deep(.p-button-icon),
.contact-cta-btn :deep(.p-button-label) {
  color: #ffffff !important;
}

@media (hover: hover) {
  .contact-cta-btn:hover {
    transform: translateY(-3px);
    background: linear-gradient(180deg, #4ade80 0%, #22c55e 45%, #15803d 100%) !important;
    box-shadow:
      0 6px 0 #14532d,
      0 14px 28px rgba(22, 163, 74, 0.45) !important;
  }

  .contact-cta-btn:active {
    transform: translateY(1px);
    box-shadow:
      0 2px 0 #14532d,
      0 4px 12px rgba(22, 163, 74, 0.3) !important;
  }
}

.contact-banner-interactive {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 50%, #a7f3d0 100%) !important;
  border-color: #6ee7b7 !important;
  transition:
    transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.28s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.28s ease;
}

html.app-dark .contact-banner-interactive {
  background: linear-gradient(135deg, #052e16 0%, #14532d 50%, #166534 100%) !important;
  border-color: #22c55e !important;
}

@media (hover: hover) {
  .contact-banner-interactive:hover,
  .contact-banner-interactive:focus-within {
    transform: translateY(-6px);
    box-shadow:
      0 4px 0 rgba(21, 128, 61, 0.35),
      0 16px 32px rgba(34, 197, 94, 0.2),
      0 6px 14px rgba(0, 0, 0, 0.06);
  }
}

.plan-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--p-text-color);
}

.plan-tagline {
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
  line-height: 1.45;
}

.plan-price-value {
  display: block;
  font-size: 2rem;
  font-weight: 800;
  line-height: 1;
  color: var(--p-text-color);
  letter-spacing: -0.03em;
}

.plan-price-detail,
.plan-price-substitute {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
}

.plan-features {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1.5rem !important;
}

.plan-features li {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--p-text-color);
}

.plan-features li i {
  flex-shrink: 0;
  margin-top: 0.15rem;
  font-size: 0.7rem;
  color: var(--p-primary-color);
}

.section-copy {
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--p-text-muted-color);
  max-width: 40rem;
}

.panel-heading {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.contact-banner-btn {
  white-space: nowrap;
}

@media (max-width: 768px) {
  .contact-banner-btn {
    white-space: normal;
    width: 100%;
  }
}

@keyframes page-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
