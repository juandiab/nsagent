<template>
  <div class="license-panel">
    <div v-if="loading" class="content-panel content-panel-padded">
      <ProgressSpinner style="width: 2rem; height: 2rem" />
    </div>

    <div v-else-if="loadError" class="content-panel content-panel-padded">
      <Message severity="error" :closable="false">
        {{ loadError }}
      </Message>
    </div>

    <div v-else class="license-layout">
      <div class="license-col license-col-main">
        <div class="content-panel content-panel-padded h-full">
          <h2 class="section-title">License</h2>
          <p v-if="!license.hasLicenseCode" class="section-copy">
            Obtain a license from Nexxus, enter your license code, or import an offline
            <code class="inline-code">.lic</code> file from activation.
          </p>
          <p v-else class="section-copy">
            Your license is registered for this installation. Remove it below to activate or import a different one.
          </p>

          <template v-if="!license.hasLicenseCode">
            <div class="activation-actions mt-4">
              <h3 class="subsection-title">1. Obtain a license</h3>
              <p class="subsection-copy">
                Open Nexxus activation in your browser or scan the QR code with your phone.
              </p>
              <form
                ref="activationFormRef"
                method="post"
                :action="LICENSE_ACTIVATION_URL"
                target="_blank"
                class="activation-post-form"
                aria-hidden="true"
              >
                <input type="hidden" name="appfingerprint" :value="activationPayload.appfingerprint" />
                <input type="hidden" name="appname" :value="activationPayload.appname" />
                <input type="hidden" name="activationdate" :value="activationPayload.activationdate" />
              </form>
              <Button
                label="Obtain license"
                icon="pi pi-external-link"
                severity="secondary"
                outlined
                :disabled="!license.appFingerprint"
                @click="submitLicenseActivation"
              />

              <div v-if="activationQrDataUrl" class="activation-qr">
                <img
                  :src="activationQrDataUrl"
                  width="220"
                  height="220"
                  alt="QR code to open license activation on your phone"
                />
                <p class="activation-qr-copy">
                  Scan with your phone camera to open license activation.
                </p>
              </div>
            </div>

            <div class="license-form mt-4 flex flex-column gap-3">
              <h3 class="subsection-title">2. Enter your license</h3>
              <p class="subsection-copy">
                Paste the code from your activation email, or import an offline
                <code class="inline-code">.lic</code> file.
              </p>

              <div class="flex flex-column gap-2">
                <label for="license-code" class="field-label">License code</label>
                <InputText
                  id="license-code"
                  :model-value="licenseCodeInput"
                  placeholder="XXXX-XXXX-XXXX-XXXX"
                  autocomplete="off"
                  spellcheck="false"
                  maxlength="19"
                  :disabled="saving || importing"
                  class="license-code-input"
                  @update:model-value="onLicenseCodeInput"
                />
                <small class="field-hint">
                  From your activation email (e.g. A9KM-ULUA-RKUA-4SYI). Letters are uppercased automatically.
                </small>
              </div>

              <div class="license-actions flex flex-wrap gap-2">
                <Button
                  label="Save license"
                  icon="pi pi-save"
                  :loading="saving"
                  :disabled="importing || !isLicenseCodeComplete"
                  @click="saveLicense"
                />
                <Button
                  label="Import offline license"
                  icon="pi pi-upload"
                  severity="secondary"
                  outlined
                  :loading="importing"
                  :disabled="saving"
                  @click="openOfflineLicensePicker"
                />
              </div>
              <input
                ref="licFileInputRef"
                type="file"
                accept=".lic,application/json"
                class="lic-file-input"
                @change="onOfflineLicenseSelected"
              />
            </div>
          </template>

          <template v-else>
            <Message
              v-if="statusMessage"
              :severity="statusSeverity"
              :closable="false"
              class="mt-4"
            >
              {{ statusMessage }}
            </Message>

            <div class="license-saved-actions mt-4">
              <Button
                label="Remove license"
                icon="pi pi-trash"
                severity="danger"
                outlined
                :loading="removing"
                @click="confirmRemoveLicense"
              />
            </div>
          </template>

          <Message
            v-if="!license.hasLicenseCode && statusMessage"
            :severity="statusSeverity"
            :closable="false"
            class="mt-4"
          >
            {{ statusMessage }}
          </Message>
        </div>
      </div>

      <div class="license-col license-col-info">
        <div
          class="content-panel content-panel-padded h-full license-details-card"
          :class="licensePlanTheme ? `license-plan-theme-${licensePlanTheme}` : null"
        >
          <div class="license-info-header">
            <h2 class="section-title">License information</h2>
            <div
              v-if="license.hasLicenseCode && licenseDetails"
              class="license-info-meta"
            >
              <Tag
                v-if="licensePlanThemeLabel"
                class="license-type-tag"
                :value="licensePlanThemeLabel"
                :severity="licensePlanTagSeverity"
              />
              <span v-else class="license-info-type license-type-value">
                {{ licenseTypeLabel(licenseDetails.licenseType) }}
              </span>
              <span class="license-info-expiry">{{ daysToExpireLabel }}</span>
            </div>
          </div>

          <template v-if="license.hasLicenseCode && licenseDetails">
            <p v-if="!hasFullLicenseDetails" class="section-copy">
              Your license code is saved. Additional details appear once the license payload is decoded from Nexxus.
            </p>

            <div class="licensed-for mt-4">
              <h3 class="licensed-for-title">Licensed for</h3>
              <p class="licensed-for-name">{{ licensedForName }}</p>
              <p class="licensed-for-email">{{ licensedForEmail }}</p>
              <p class="licensed-for-company">{{ companyLabel }}</p>
            </div>

            <dl class="license-details-list mt-4">
              <div class="license-details-row">
                <dt>License code</dt>
                <dd class="license-code-display">
                  <code>{{ displayedLicenseCode }}</code>
                  <Button
                    v-if="licenseDetails.licenseCode"
                    :icon="revealLicenseCode ? 'pi pi-eye-slash' : 'pi pi-eye'"
                    severity="secondary"
                    text
                    rounded
                    size="small"
                    class="license-code-toggle"
                    :aria-label="revealLicenseCode ? 'Hide license code' : 'Show license code'"
                    @click="revealLicenseCode = !revealLicenseCode"
                  />
                  <Button
                    v-if="licenseDetails.licenseCode"
                    icon="pi pi-copy"
                    severity="secondary"
                    text
                    rounded
                    size="small"
                    class="license-code-toggle"
                    aria-label="Copy license code"
                    @click="copyLicenseCode"
                  />
                </dd>
              </div>
            </dl>
          </template>

          <p v-else-if="license.hasLicenseCode" class="license-info-empty mt-4">
            Your license code is saved. Additional details appear once the license payload is decoded from Nexxus.
          </p>

          <p v-else class="license-info-empty mt-4">
            Register or import a license to view type, expiration, and customer details here.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import QRCode from 'qrcode'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'
import { LICENSE_PLAN_THEME_LABELS, resolveLicensePlanTheme } from '../config/licensePlanThemes'
import { JPILOT_APP_NAME } from '../config/product'
import { invalidateLicenseGateCache, licenseActivationRequired } from '../services/licenseGate'
import { getLicense, importOfflineLicense, removeLicense, saveLicenseCode } from '../services/system'

const confirm = useConfirm()
const toast = useToast()
const route = useRoute()
const router = useRouter()

const LICENSE_ACTIVATION_URL = 'https://nexxus-tech.com/licensing/activate'
const LICENSE_CODE_PATTERN = /^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/

/** Format as XXXX-XXXX-XXXX-XXXX, uppercase alphanumeric only. */
function formatLicenseCodeInput(raw) {
  const chars = String(raw ?? '')
    .replace(/[^A-Za-z0-9]/g, '')
    .toUpperCase()
    .slice(0, 16)
  if (!chars) return ''
  const parts = []
  for (let i = 0; i < chars.length; i += 4) {
    parts.push(chars.slice(i, i + 4))
  }
  return parts.join('-')
}

function onLicenseCodeInput(value) {
  licenseCodeInput.value = formatLicenseCodeInput(value)
}

const loading = ref(true)
const saving = ref(false)
const importing = ref(false)
const removing = ref(false)
const loadError = ref('')
const licFileInputRef = ref(null)
const license = ref({
  appFingerprint: '',
  appName: JPILOT_APP_NAME,
  activationDate: '',
  hasLicenseCode: false,
  status: 'pending',
  message: '',
  syncError: null,
  obtainedOffline: false,
  details: null
})
const licenseCodeInput = ref('')
const revealLicenseCode = ref(false)
const activationQrDataUrl = ref('')
const activationFormRef = ref(null)

const activationPayload = computed(() => ({
  appfingerprint: license.value.appFingerprint,
  appname: license.value.appName || JPILOT_APP_NAME,
  activationdate: license.value.activationDate || new Date().toISOString()
}))

const isLicenseCodeComplete = computed(() => LICENSE_CODE_PATTERN.test(licenseCodeInput.value))

const licenseDetails = computed(() => license.value.details)

const licensePlanTheme = computed(() => {
  if (!license.value.hasLicenseCode) return null
  const type = licenseDetails.value?.licenseType ?? license.value.licenseType
  return resolveLicensePlanTheme(type)
})

const licensePlanThemeLabel = computed(() => {
  const theme = licensePlanTheme.value
  if (!theme) return null
  return LICENSE_PLAN_THEME_LABELS[theme] ?? null
})

const licensePlanTagSeverity = computed(() => {
  const theme = licensePlanTheme.value
  if (theme === 'free') return 'success'
  if (theme === 'trial') return 'warn'
  if (theme === 'enterprise') return 'info'
  if (theme === 'enterprise-pro') return 'secondary'
  return 'secondary'
})

const hasFullLicenseDetails = computed(() => {
  const d = licenseDetails.value
  if (!d) return false
  return Boolean(
    d.licenseType ||
      d.expirationDate != null ||
      d.daysToExpire != null ||
      d.customerName ||
      d.customerEmail ||
      d.company
  )
})

const daysToExpireLabel = computed(() => {
  const days = licenseDetails.value?.daysToExpire
  if (days == null) return '—'
  if (days === 0) return 'Expires today'
  if (days === 1) return '1 day'
  return `${days} days`
})

const licensedForName = computed(() => displayValue(licenseDetails.value?.customerName))

const licensedForEmail = computed(() => displayValue(licenseDetails.value?.customerEmail))

const companyLabel = computed(() => {
  const company = licenseDetails.value?.company
  const text = String(company ?? '').trim()
  return text || 'Personal Use'
})

const displayedLicenseCode = computed(() => {
  const code = licenseDetails.value?.licenseCode
  if (!code) return '—'
  return revealLicenseCode.value ? String(code) : maskLicenseCode(code)
})

function displayValue(value) {
  if (value == null) return '—'
  const text = String(value).trim()
  return text ? text : '—'
}

function licenseTypeLabel(type) {
  const theme = resolveLicensePlanTheme(type)
  if (theme && LICENSE_PLAN_THEME_LABELS[theme]) return LICENSE_PLAN_THEME_LABELS[theme]
  return displayValue(type)
}

function maskLicenseCode(code) {
  return String(code).replace(/[A-Za-z0-9]/g, '•')
}

function maybeRedirectAfterActivation() {
  const redirect = route.query.redirect
  if (typeof redirect !== 'string' || !redirect.startsWith('/') || redirect.startsWith('//')) {
    return
  }
  if (licenseActivationRequired(license.value)) return
  router.replace(redirect)
}

async function copyLicenseCode() {
  const code = licenseDetails.value?.licenseCode
  if (!code) return
  try {
    await navigator.clipboard.writeText(String(code))
    toast.add({
      severity: 'success',
      summary: 'Copied',
      detail: 'License code copied to clipboard.',
      life: 3000
    })
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Copy failed',
      detail: 'Could not copy license code.',
      life: 3000
    })
  }
}

const statusMessage = computed(() => {
  if (license.value.status === 'active' || license.value.status === 'renewed') {
    const base = license.value.message || 'License is active.'
    if (license.value.obtainedOffline) {
      return `${base} Offline license — Nexxus sync is disabled.`
    }
    return base
  }
  if (license.value.syncError) return license.value.syncError
  if (license.value.message) return license.value.message
  if (license.value.status === 'pending' && !license.value.hasLicenseCode) {
    return 'Enter your license code after completing activation.'
  }
  if (license.value.status === 'deactivated') {
    return license.value.message || 'License was deactivated.'
  }
  if (license.value.status === 'missing') {
    return license.value.message || 'No license found for this deployment.'
  }
  return ''
})

const statusSeverity = computed(() => {
  const status = license.value.status
  if (
    license.value.syncError ||
    status === 'expired' ||
    status === 'deactivated' ||
    status === 'missing'
  ) {
    return 'error'
  }
  if (status === 'active' || status === 'renewed') return 'success'
  if (status === 'pending') return 'info'
  return 'warn'
})

/** GET URL for QR codes (phone camera). */
function buildActivationUrl() {
  const params = new URLSearchParams(activationPayload.value)
  return `${LICENSE_ACTIVATION_URL}?${params.toString()}`
}

function submitLicenseActivation() {
  if (!license.value.appFingerprint || !activationFormRef.value) return
  activationFormRef.value.submit()
}

async function refreshActivationQr() {
  if (!license.value.appFingerprint) {
    activationQrDataUrl.value = ''
    return
  }
  activationQrDataUrl.value = await QRCode.toDataURL(buildActivationUrl(), {
    errorCorrectionLevel: 'M',
    margin: 2,
    width: 220
  })
}

async function saveLicense() {
  saving.value = true
  try {
    license.value = await saveLicenseCode(licenseCodeInput.value)
    invalidateLicenseGateCache()
    licenseCodeInput.value = ''
    maybeRedirectAfterActivation()
  } catch (err) {
    const detail = err?.response?.data?.detail
    license.value = {
      ...license.value,
      syncError: typeof detail === 'string' ? detail : err?.message || 'Could not save license.'
    }
  } finally {
    saving.value = false
  }
}

function openOfflineLicensePicker() {
  licFileInputRef.value?.click()
}

function confirmRemoveLicense() {
  confirm.require({
    message:
      'Remove the current license from this installation? Your installation record is kept so you can obtain or import a new license.',
    header: 'Remove license',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      removing.value = true
      try {
        license.value = await removeLicense()
        invalidateLicenseGateCache()
        licenseCodeInput.value = ''
        revealLicenseCode.value = false
        toast.add({
          severity: 'success',
          summary: 'License removed',
          detail: 'You can activate or import a new license for this installation.',
          life: 5000
        })
      } catch (err) {
        const detail = err?.response?.data?.detail
        toast.add({
          severity: 'error',
          summary: 'Remove failed',
          detail: typeof detail === 'string' ? detail : err?.message || 'Could not remove license.',
          life: 5000
        })
      } finally {
        removing.value = false
      }
    }
  })
}

async function onOfflineLicenseSelected(event) {
  const file = event.target?.files?.[0]
  if (!file) return
  importing.value = true
  try {
    license.value = await importOfflineLicense(file)
    invalidateLicenseGateCache()
    const code = license.value.details?.licenseCode
    if (code) licenseCodeInput.value = code
    maybeRedirectAfterActivation()
  } catch (err) {
    const detail = err?.response?.data?.detail
    license.value = {
      ...license.value,
      syncError: typeof detail === 'string' ? detail : err?.message || 'Could not import license file.'
    }
  } finally {
    importing.value = false
    if (event.target) event.target.value = ''
  }
}

onMounted(async () => {
  try {
    license.value = await getLicense()
    await refreshActivationQr()
  } catch (err) {
    loadError.value = err?.response?.data?.detail || err?.message || 'Could not load license.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.license-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
  gap: 1rem;
  align-items: stretch;
}

.license-col {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.license-col .content-panel {
  flex: 1;
  width: 100%;
}

@media (max-width: 991px) {
  .license-layout {
    grid-template-columns: 1fr;
  }
}

.field-label {
  font-size: 0.875rem;
  font-weight: 600;
}

.field-hint {
  color: var(--p-text-muted-color);
  font-size: 0.8125rem;
}

.license-code-input {
  max-width: 20rem;
  font-family: ui-monospace, monospace;
  letter-spacing: 0.04em;
}

.inline-code {
  font-family: ui-monospace, monospace;
  font-size: 0.875em;
}

.lic-file-input {
  display: none;
}

.activation-post-form {
  display: none;
}

.subsection-title {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 600;
}

.subsection-copy {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
  line-height: 1.45;
}

.activation-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1.25rem;
}

.activation-qr {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
}

.activation-qr img {
  display: block;
  border-radius: var(--p-border-radius);
  background: #fff;
  padding: 0.5rem;
  border: 1px solid var(--p-content-border-color);
}

.activation-qr-copy {
  margin: 0;
  max-width: 16rem;
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
  line-height: 1.45;
}

.license-details-list {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.license-details-row {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.license-details-row dt {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.license-details-row dd {
  margin: 0;
  font-size: 0.9375rem;
}

.license-details-row code {
  font-family: ui-monospace, monospace;
  letter-spacing: 0.04em;
}

.license-code-display {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.license-code-toggle {
  flex-shrink: 0;
}

.licensed-for {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--p-content-border-color);
}

.licensed-for-title {
  margin: 0 0 0.35rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.licensed-for-name {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--p-text-color);
  line-height: 1.35;
}

.licensed-for-email {
  margin: 0;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  line-height: 1.4;
}

.licensed-for-company {
  margin: 0;
  font-size: 0.875rem;
  color: var(--p-text-color);
  line-height: 1.4;
}

.license-saved-actions {
  padding-top: 0.25rem;
}

.license-info-empty {
  margin: 0;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  line-height: 1.55;
}

.license-details-card {
  transition:
    background 0.25s ease,
    border-color 0.25s ease;
}

.license-info-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.license-info-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.35rem;
  flex-shrink: 0;
  text-align: right;
}

.license-info-type {
  font-size: 0.9375rem;
  font-weight: 600;
  line-height: 1.2;
}

.license-info-expiry {
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
  line-height: 1.3;
}

.license-plan-theme-free {
  background: linear-gradient(160deg, #f8fafc 0%, #f0fdf4 55%, #ecfdf5 100%);
  border-color: #bbf7d0;
}

html.app-dark .license-plan-theme-free {
  background: linear-gradient(160deg, #0f172a 0%, #14532d 45%, #052e16 100%);
  border-color: #166534;
}

.license-plan-theme-free .license-type-value {
  color: #16a34a;
  font-weight: 600;
}

html.app-dark .license-plan-theme-free .license-type-value {
  color: #86efac;
}

.license-plan-theme-trial {
  background: linear-gradient(160deg, #fffbeb 0%, #fff7ed 55%, #ffedd5 100%);
  border-color: #fed7aa;
}

html.app-dark .license-plan-theme-trial {
  background: linear-gradient(160deg, #1c1917 0%, #431407 45%, #292524 100%);
  border-color: #9a3412;
}

.license-plan-theme-trial .license-type-value {
  color: #c2410c;
  font-weight: 600;
}

html.app-dark .license-plan-theme-trial .license-type-value {
  color: #fb923c;
}

.license-plan-theme-enterprise {
  background: linear-gradient(160deg, #eff6ff 0%, #dbeafe 50%, #bfdbfe 100%);
  border-color: #60a5fa;
}

html.app-dark .license-plan-theme-enterprise {
  background: linear-gradient(160deg, #0c1929 0%, #1e3a8a 50%, #172554 100%);
  border-color: #3b82f6;
}

.license-plan-theme-enterprise .license-type-value {
  color: #2563eb;
  font-weight: 600;
}

html.app-dark .license-plan-theme-enterprise .license-type-value {
  color: #93c5fd;
}

.license-plan-theme-enterprise-pro {
  background: linear-gradient(160deg, #faf5ff 0%, #ede9fe 45%, #ddd6fe 100%);
  border-color: #a78bfa;
}

html.app-dark .license-plan-theme-enterprise-pro {
  background: linear-gradient(160deg, #1a0b2e 0%, #4c1d95 50%, #2e1065 100%);
  border-color: #8b5cf6;
}

.license-plan-theme-enterprise-pro .license-type-value {
  color: #7c3aed;
  font-weight: 600;
}

html.app-dark .license-plan-theme-enterprise-pro .license-type-value {
  color: #c4b5fd;
}
</style>
