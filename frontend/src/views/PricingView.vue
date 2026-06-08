<template>
  <div class="page">
    <div class="welcome-panel plans-hero mb-5">
      <div class="plans-hero-brand">
        <img :src="logoSrc" alt="JPilot" class="plans-hero-logo" width="40" height="40" />
        <p class="plans-hero-eyebrow m-0">
          <span class="plans-hero-product">JPilot</span>
          <span class="plans-hero-separator" aria-hidden="true">·</span>
          <a
            :href="NEXXUS_TECH.websiteUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="plans-hero-vendor"
          >Nexxus Tech</a>
        </p>
      </div>
      <h1 class="plans-hero-title m-0">Early access, unlimited, on-premises</h1>
      <p class="plans-hero-copy m-0">
        The core platform is in <strong>early access</strong> — unlimited NetScalers and LLM providers,
        deployed <strong>on-prem</strong> with Docker. Credentials and config stay in your network.
        Encrypted secrets, JWT sessions, optional passkeys, and containers you can monitor with your own tooling.
      </p>
    </div>

    <section class="plan-section mb-5" aria-label="Plan options">
      <div class="plan-mobile-tabs">
        <SelectButton
          v-model="selectedPlanId"
          :options="planTabOptions"
          option-label="label"
          option-value="value"
          :allow-empty="false"
          aria-label="Select a plan to preview"
        />
      </div>

      <div class="plan-cards-grid">
        <div
          v-for="plan in PRICING_PLANS"
          :key="plan.id"
          class="plan-card-col"
          :class="{ 'plan-card-col-hidden-mobile': selectedPlanId !== plan.id }"
        >
          <div
            class="plan-card h-full flex flex-column"
            :class="[
              `plan-card-${plan.id}`,
              {
                'plan-card-featured': isCurrentPlan(plan),
                'plan-card-trial': licensePlanTheme === 'trial' && isCurrentPlan(plan),
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
                  v-if="isCurrentPlan(plan)"
                  :value="currentPlanTagLabel(plan)"
                  :severity="currentPlanTagSeverity(plan)"
                />
              </div>

              <div v-if="plan.priceLabel" class="plan-price mt-4">
                <span class="plan-price-value">{{ plan.priceLabel }}</span>
                <span class="plan-price-detail">{{ plan.priceDetail }}</span>
              </div>
              <p v-else class="plan-price-substitute m-0 mt-4">{{ plan.priceDetail }}</p>
            </div>

            <p class="plan-card-hint m-0 mt-3">
              {{ planCardHint(plan) }}
            </p>

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
    </section>

    <section class="comparison-section mb-5" aria-labelledby="comparison-heading">
      <div class="comparison-header mb-3">
        <h2 id="comparison-heading" class="comparison-title m-0">What's included</h2>
        <p class="comparison-copy m-0 mt-2">
          Compare plans side by side on desktop, or switch tabs above on mobile to see what each tier includes.
        </p>
      </div>

      <div class="comparison-desktop content-panel">
        <div class="comparison-table-wrap">
          <table class="comparison-table">
            <thead>
              <tr>
                <th scope="col" class="comparison-feature-col">Feature</th>
                <th
                  v-for="plan in PRICING_PLANS"
                  :key="plan.id"
                  scope="col"
                  class="comparison-plan-col"
                  :class="[
                    `comparison-plan-col-${plan.id}`,
                    { 'comparison-plan-col-current': isCurrentPlan(plan) }
                  ]"
                >
                  <span class="comparison-plan-name">{{ plan.name }}</span>
                  <Tag
                    v-if="isCurrentPlan(plan)"
                    :value="currentPlanTagLabel(plan)"
                    :severity="currentPlanTagSeverity(plan)"
                    class="comparison-current-tag"
                  />
                </th>
              </tr>
            </thead>
            <tbody>
              <template v-for="group in PLAN_FEATURE_GROUPS" :key="group.id">
                <tr class="comparison-group-row">
                  <th scope="rowgroup" :colspan="PRICING_PLANS.length + 1">
                    <span class="comparison-group-title">{{ group.title }}</span>
                    <span class="comparison-group-subtitle">{{ group.subtitle }}</span>
                  </th>
                </tr>
                <tr
                  v-for="feature in group.features"
                  :key="`${group.id}-${featureKey(feature)}`"
                  class="comparison-feature-row"
                >
                  <th scope="row" class="comparison-feature-label">{{ featureLabel(feature) }}</th>
                  <td
                    v-for="plan in PRICING_PLANS"
                    :key="`${group.id}-${featureKey(feature)}-${plan.id}`"
                    class="comparison-check-cell"
                    :class="{ 'comparison-check-cell-current': isCurrentPlan(plan) }"
                  >
                    <span
                      v-if="planIncludesGroup(plan.id, group)"
                      class="comparison-check"
                      :class="`comparison-check-${plan.id}`"
                      aria-label="Included"
                    >
                      <i class="pi pi-check" aria-hidden="true" />
                    </span>
                    <span v-else class="comparison-dash" aria-label="Not included">—</span>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
        <div v-if="planFootnotes.length" class="comparison-footnotes">
          <p
            v-for="(footnote, index) in planFootnotes"
            :key="index"
            class="comparison-footnote m-0"
          >
            <span class="comparison-footnote-marker">{{ footnote.marker }}</span>
            {{ footnote.text }}
          </p>
        </div>
      </div>

      <div class="comparison-mobile">
        <div
          v-for="group in mobileComparisonGroups"
          :key="group.id"
          class="comparison-mobile-group content-panel content-panel-padded"
          :class="`comparison-mobile-group-${group.id}`"
        >
          <div class="comparison-mobile-group-header">
            <h3 class="comparison-mobile-group-title m-0">{{ group.title }}</h3>
            <p class="comparison-mobile-group-subtitle m-0 mt-1">{{ group.subtitle }}</p>
          </div>
          <ul class="comparison-mobile-features m-0 p-0 list-none">
            <li v-for="feature in group.features" :key="featureKey(feature)">
              <i class="pi pi-check" aria-hidden="true" />
              <span>{{ featureLabel(feature) }}</span>
            </li>
          </ul>
        </div>
        <div v-if="planFootnotes.length" class="comparison-footnotes comparison-footnotes-mobile">
          <p
            v-for="(footnote, index) in planFootnotes"
            :key="index"
            class="comparison-footnote m-0"
          >
            <span class="comparison-footnote-marker">{{ footnote.marker }}</span>
            {{ footnote.text }}
          </p>
        </div>
      </div>
    </section>

    <section class="pricing-bottom">
      <div class="pricing-highlights">
        <div
          v-for="item in PLATFORM_HIGHLIGHTS"
          :key="item.title"
          class="highlight-card flex align-items-start gap-2"
        >
          <i :class="['highlight-icon', item.icon]" />
          <div class="highlight-body min-w-0">
            <h3 class="highlight-title">{{ item.title }}</h3>
            <p class="highlight-copy m-0">{{ item.description }}</p>
          </div>
        </div>
      </div>
      <div
        class="content-panel content-panel-padded contact-banner contact-banner-interactive contact-banner-side"
      >
        <div class="contact-banner-inner flex flex-column h-full justify-content-between gap-3">
          <div>
            <h3 class="panel-heading m-0">Need Enterprise?</h3>
            <p class="section-copy contact-banner-copy m-0 mt-2">
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
            class="contact-banner-btn contact-cta-btn w-full"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import Button from 'primevue/button'
import SelectButton from 'primevue/selectbutton'
import Tag from 'primevue/tag'
import logoLight from '../assets/JPilot-logo-big.svg'
import logoDark from '../assets/JPilot-logo-big-black.svg'
import { licenseTypeToPlanId, resolveLicensePlanTheme } from '../config/licensePlanThemes'
import { NEXXUS_TECH } from '../config/nexxusTech'
import {
  comparisonFootnotes,
  featureKey,
  featureLabel,
  groupsForPlan,
  PLAN_FEATURE_GROUPS,
  planIncludesGroup,
  PLATFORM_HIGHLIGHTS,
  PRICING_PLANS
} from '../config/pricingPlans'
import { getLicense } from '../services/system'
import { getTheme } from '../services/theme'

const license = ref(null)
const selectedPlanId = ref('free')
const theme = ref(getTheme())

const logoSrc = computed(() => (theme.value === 'dark' ? logoDark : logoLight))

const planTabOptions = PRICING_PLANS.map((plan) => ({
  label: plan.shortName,
  value: plan.id
}))

const activePlanId = computed(() => {
  if (!license.value?.hasLicenseCode) return 'free'
  const type = license.value.details?.licenseType ?? license.value.licenseType
  const theme = resolveLicensePlanTheme(type)
  if (theme === 'trial') return 'free'
  return licenseTypeToPlanId(type) || 'free'
})

const licensePlanTheme = computed(() => {
  if (!license.value?.hasLicenseCode) return 'free'
  const type = license.value.details?.licenseType ?? license.value.licenseType
  return resolveLicensePlanTheme(type)
})

const mobileComparisonGroups = computed(() => groupsForPlan(selectedPlanId.value))

const planFootnotes = comparisonFootnotes()

watch(activePlanId, (planId) => {
  selectedPlanId.value = planId
}, { immediate: true })

function isCurrentPlan(plan) {
  return activePlanId.value === plan.id
}

function currentPlanTagLabel(plan) {
  if (!isCurrentPlan(plan)) return 'Current'
  if (licensePlanTheme.value === 'trial') return 'Trial'
  return 'Current'
}

function currentPlanTagSeverity(plan) {
  if (!isCurrentPlan(plan)) return 'success'
  if (licensePlanTheme.value === 'trial') return 'warn'
  return 'success'
}

function planCardHint(plan) {
  if (plan.id === 'free') {
    return 'Full platform while we refine the offering. See what’s included below.'
  }
  if (plan.id === 'enterprise') {
    return 'Adds identity, scoped vendor personalization, ADC depth, and engineer-led rollout on top of Early Access.'
  }
  return 'Adds advanced WAF programs, Stack Calibration Studio, and on-demand expert support via Support Credits.'
}

onMounted(async () => {
  window.addEventListener('jpilot-theme-change', onThemeChange)
  try {
    license.value = await getLicense()
  } catch {
    // Plans page works without license data.
  }
})

onUnmounted(() => {
  window.removeEventListener('jpilot-theme-change', onThemeChange)
})

function onThemeChange(event) {
  theme.value = event.detail
}
</script>

<style scoped>
.page {
  animation: page-in 0.35s ease;
}

.plans-hero {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.plans-hero-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.plans-hero-logo {
  display: block;
  width: 2.5rem;
  height: 2.5rem;
  flex-shrink: 0;
}

.plans-hero-eyebrow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1.3;
  color: var(--p-text-muted-color);
}

.plans-hero-product {
  color: var(--p-text-color);
}

.plans-hero-separator {
  color: var(--p-text-muted-color);
  opacity: 0.65;
}

.plans-hero-vendor {
  color: var(--p-primary-color);
  text-decoration: none;
}

.plans-hero-vendor:hover {
  text-decoration: underline;
}

.plans-hero-title {
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.25;
  color: var(--p-text-color);
}

.plans-hero-copy {
  font-size: 0.8125rem;
  line-height: 1.55;
  color: var(--p-text-muted-color);
  max-width: 42rem;
}

.plans-hero-copy strong {
  color: var(--p-text-color);
  font-weight: 600;
}

.plan-mobile-tabs {
  display: none;
  margin-bottom: 1rem;
}

.plan-mobile-tabs :deep(.p-selectbutton) {
  display: flex;
  width: 100%;
}

.plan-mobile-tabs :deep(.p-togglebutton) {
  flex: 1 1 0;
  min-width: 0;
}

.plan-mobile-tabs :deep(.p-togglebutton .p-togglebutton-content) {
  padding: 0.5rem 0.35rem;
  font-size: 0.75rem;
  line-height: 1.2;
  white-space: normal;
  text-align: center;
}

.plan-cards-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.plan-card-hint {
  flex: 1;
  font-size: 0.8125rem;
  line-height: 1.55;
  color: var(--p-text-muted-color);
}

.comparison-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--p-text-color);
}

.comparison-copy {
  font-size: 0.8125rem;
  line-height: 1.55;
  color: var(--p-text-muted-color);
  max-width: 42rem;
}

.comparison-desktop {
  padding: 0;
  overflow: hidden;
}

.comparison-mobile {
  display: none;
  flex-direction: column;
  gap: 0.75rem;
}

.comparison-table-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.comparison-table {
  width: 100%;
  min-width: 40rem;
  border-collapse: collapse;
}

.comparison-table th,
.comparison-table td {
  border-bottom: 1px solid var(--p-content-border-color);
  vertical-align: middle;
}

.comparison-table thead th {
  padding: 1rem 0.75rem;
  font-size: 0.8125rem;
  font-weight: 600;
  text-align: center;
  color: var(--p-text-color);
  background: var(--p-content-background);
}

.comparison-feature-col {
  width: 42%;
  text-align: left !important;
  padding-left: 1.25rem !important;
}

.comparison-plan-col {
  width: calc(58% / 3);
}

.comparison-plan-col-current {
  background: color-mix(in srgb, var(--p-primary-color) 6%, var(--p-content-background));
}

.comparison-plan-name {
  display: block;
  font-size: 0.8125rem;
  line-height: 1.3;
}

.comparison-current-tag {
  margin-top: 0.35rem;
}

.comparison-group-row th {
  padding: 0.875rem 1.25rem;
  text-align: left;
  background: color-mix(in srgb, var(--p-content-border-color) 35%, var(--p-content-background));
  border-bottom: 1px solid var(--p-content-border-color);
}

.comparison-group-title {
  display: block;
  font-size: 0.8125rem;
  font-weight: 700;
  color: var(--p-text-color);
}

.comparison-group-subtitle {
  display: block;
  margin-top: 0.125rem;
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--p-text-muted-color);
}

.comparison-feature-row th,
.comparison-feature-row td {
  padding: 0.625rem 0.75rem;
}

.comparison-feature-label {
  padding-left: 1.25rem !important;
  font-size: 0.75rem;
  font-weight: 500;
  line-height: 1.45;
  text-align: left;
  color: var(--p-text-color);
}

.comparison-check-cell {
  text-align: center;
}

.comparison-check-cell-current {
  background: color-mix(in srgb, var(--p-primary-color) 4%, transparent);
}

.comparison-check {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.375rem;
  height: 1.375rem;
  border-radius: 999px;
}

.comparison-check i {
  font-size: 0.65rem;
  font-weight: 700;
}

.comparison-check-free {
  color: #16a34a;
  background: #dcfce7;
}

.comparison-check-enterprise {
  color: #2563eb;
  background: #dbeafe;
}

.comparison-check-enterprise-pro {
  color: #7c3aed;
  background: #ede9fe;
}

html.app-dark .comparison-check-free {
  color: #86efac;
  background: rgba(22, 163, 74, 0.2);
}

html.app-dark .comparison-check-enterprise {
  color: #93c5fd;
  background: rgba(37, 99, 235, 0.2);
}

html.app-dark .comparison-check-enterprise-pro {
  color: #c4b5fd;
  background: rgba(124, 58, 237, 0.2);
}

.comparison-dash {
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.comparison-footnotes {
  padding: 0.875rem 1.25rem 1.125rem;
  border-top: 1px solid var(--p-content-border-color);
  background: color-mix(in srgb, var(--p-content-border-color) 18%, var(--p-content-background));
}

.comparison-footnotes-mobile {
  display: none;
  margin-top: 0.25rem;
  padding: 0.875rem 1rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: var(--content-radius);
  background: color-mix(in srgb, var(--p-content-border-color) 18%, var(--p-content-background));
}

.comparison-footnote {
  font-size: 0.6875rem;
  line-height: 1.55;
  color: var(--p-text-muted-color);
}

.comparison-footnote + .comparison-footnote {
  margin-top: 0.5rem;
}

.comparison-footnote-marker {
  font-weight: 700;
  color: var(--p-text-color);
}

.comparison-mobile-group {
  border: 1px solid var(--p-content-border-color);
}

.comparison-mobile-group-base {
  border-color: #bbf7d0;
  background: linear-gradient(160deg, #f8fafc 0%, #f0fdf4 55%, #ecfdf5 100%);
}

.comparison-mobile-group-enterprise {
  border-color: #60a5fa;
  background: linear-gradient(160deg, #eff6ff 0%, #dbeafe 50%, #bfdbfe 100%);
}

.comparison-mobile-group-enterprise-pro {
  border-color: #a78bfa;
  background: linear-gradient(160deg, #faf5ff 0%, #ede9fe 45%, #ddd6fe 100%);
}

html.app-dark .comparison-mobile-group-base {
  border-color: #166534;
  background: linear-gradient(160deg, #0f172a 0%, #14532d 45%, #052e16 100%);
}

html.app-dark .comparison-mobile-group-enterprise {
  border-color: #3b82f6;
  background: linear-gradient(160deg, #0c1929 0%, #1e3a8a 50%, #172554 100%);
}

html.app-dark .comparison-mobile-group-enterprise-pro {
  border-color: #8b5cf6;
  background: linear-gradient(160deg, #1a0b2e 0%, #4c1d95 50%, #2e1065 100%);
}

.comparison-mobile-group-title {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--p-text-color);
}

.comparison-mobile-group-subtitle {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

.comparison-mobile-features {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  margin-top: 1rem !important;
}

.comparison-mobile-features li {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--p-text-color);
}

.comparison-mobile-group-base .comparison-mobile-features li i {
  color: #16a34a;
}

.comparison-mobile-group-enterprise .comparison-mobile-features li i {
  color: #2563eb;
}

.comparison-mobile-group-enterprise-pro .comparison-mobile-features li i {
  color: #7c3aed;
}

html.app-dark .comparison-mobile-group-base .comparison-mobile-features li i {
  color: #86efac;
}

html.app-dark .comparison-mobile-group-enterprise .comparison-mobile-features li i {
  color: #93c5fd;
}

html.app-dark .comparison-mobile-group-enterprise-pro .comparison-mobile-features li i {
  color: #c4b5fd;
}

.comparison-mobile-features li i {
  flex-shrink: 0;
  margin-top: 0.15rem;
  font-size: 0.7rem;
}

.pricing-bottom {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: 1rem;
  align-items: stretch;
  width: 100%;
}

.pricing-highlights {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: repeat(3, minmax(0, auto));
  gap: 0.5rem;
  min-width: 0;
}

.contact-banner-side {
  height: 100%;
  min-height: 100%;
}

.contact-banner-copy {
  max-width: none;
}

.contact-banner-side .section-copy {
  font-size: 0.8125rem;
  line-height: 1.5;
}

.highlight-card {
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: calc(var(--content-radius) * 0.85);
  padding: 0.5rem 0.625rem;
}

.highlight-icon {
  flex-shrink: 0;
  font-size: 0.875rem;
  line-height: 1;
  color: var(--p-primary-color);
  margin-top: 0.1rem;
}

.highlight-title {
  margin: 0 0 0.125rem;
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1.25;
  color: var(--p-text-color);
}

.highlight-copy {
  font-size: 0.6875rem;
  line-height: 1.35;
  color: var(--p-text-muted-color);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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

.plan-card-trial.plan-card-free {
  background: linear-gradient(160deg, #fffbeb 0%, #fff7ed 55%, #ffedd5 100%);
  border-color: #fed7aa;
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

html.app-dark .plan-card-trial.plan-card-free {
  background: linear-gradient(160deg, #1c1917 0%, #431407 45%, #292524 100%);
  border-color: #9a3412;
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

@media (max-width: 991px) {
  .plan-mobile-tabs {
    display: block;
  }

  .plan-cards-grid {
    grid-template-columns: 1fr;
  }

  .plan-card-col-hidden-mobile {
    display: none;
  }

  .comparison-desktop {
    display: none;
  }

  .comparison-mobile {
    display: flex;
  }

  .comparison-footnotes-mobile {
    display: block;
  }

  .comparison-copy {
    display: none;
  }
}

@media (max-width: 768px) {
  .pricing-bottom {
    grid-template-columns: 1fr;
  }

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

@media (max-height: 900px) {
  .plans-hero {
    gap: 0.375rem;
  }

  .plans-hero-logo {
    width: 2.125rem;
    height: 2.125rem;
  }

  .plans-hero-title {
    font-size: 1.0625rem;
  }

  .plans-hero-copy {
    font-size: 0.75rem;
    line-height: 1.45;
  }

  .highlight-card {
    padding: 0.375rem 0.5rem;
  }

  .highlight-icon {
    font-size: 0.75rem;
  }

  .highlight-title {
    font-size: 0.6875rem;
  }

  .highlight-copy {
    font-size: 0.625rem;
    line-height: 1.3;
  }

  .contact-banner-side .section-copy {
    font-size: 0.75rem;
  }

  .plan-card {
    padding: 1rem;
  }

  .comparison-title {
    font-size: 1rem;
  }

  .comparison-table thead th,
  .comparison-feature-label {
    font-size: 0.6875rem;
  }
}
</style>
