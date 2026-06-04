<template>
  <div class="license-panel flex flex-column gap-4">
    <div class="content-panel content-panel-padded">
      <h2 class="section-title">License</h2>
      <p class="section-copy">
        Obtain a license from Nexxus, enter your license code, or import an offline
        <code class="inline-code">.lic</code> file from activation.
      </p>

      <div v-if="loading" class="mt-4">
        <ProgressSpinner style="width: 2rem; height: 2rem" />
      </div>

      <Message v-else-if="loadError" severity="error" :closable="false" class="mt-4">
        {{ loadError }}
      </Message>

      <template v-else>
        <div class="license-form mt-4 flex flex-column gap-3">
          <div class="flex flex-column gap-2">
            <label for="license-code" class="field-label">License code</label>
            <InputText
              id="license-code"
              :model-value="licenseCodeInput"
              placeholder="XXXX-XXXX-XXXX-XXXX"
              autocomplete="off"
              spellcheck="false"
              maxlength="19"
              :disabled="saving || importing || removing"
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
              :disabled="importing || removing || !isLicenseCodeComplete"
              @click="saveLicense"
            />
            <Button
              label="Import offline license"
              icon="pi pi-upload"
              severity="secondary"
              outlined
              :loading="importing"
              :disabled="saving || removing"
              @click="openOfflineLicensePicker"
            />
            <Button
              v-if="license.hasLicenseCode"
              label="Remove license"
              icon="pi pi-trash"
              severity="danger"
              outlined
              :loading="removing"
              :disabled="saving || importing"
              @click="confirmRemoveLicense"
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

        <Message
          v-if="statusMessage"
          :severity="statusSeverity"
          :closable="false"
          class="mt-4"
        >
          {{ statusMessage }}
        </Message>

        <div class="activation-actions mt-4">
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
      </template>
    </div>

    <div
      v-if="!loading && !loadError && licenseDetails"
      class="content-panel content-panel-padded license-details-card"
    >
      <h2 class="section-title">License information</h2>
      <p v-if="!hasFullLicenseDetails" class="section-copy">
        Your license code is saved. Additional details appear once the license payload is decoded from Nexxus.
      </p>

      <dl class="license-details-list mt-4">
        <div class="license-details-row">
          <dt>License type</dt>
          <dd>{{ displayValue(licenseDetails.licenseType) }}</dd>
        </div>
        <div class="license-details-row">
          <dt>License code</dt>
          <dd><code>{{ displayValue(licenseDetails.licenseCode) }}</code></dd>
        </div>
        <div class="license-details-row">
          <dt>Days to expire</dt>
          <dd>{{ daysToExpireLabel }}</dd>
        </div>
        <div class="license-details-row">
          <dt>Name</dt>
          <dd>{{ displayValue(licenseDetails.customerName) }}</dd>
        </div>
        <div class="license-details-row">
          <dt>Email</dt>
          <dd>{{ displayValue(licenseDetails.customerEmail) }}</dd>
        </div>
        <div class="license-details-row">
          <dt>Company</dt>
          <dd>{{ displayValue(licenseDetails.company) }}</dd>
        </div>
      </dl>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import QRCode from 'qrcode'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import { JPILOT_APP_NAME } from '../config/product'
import { getLicense, importOfflineLicense, removeLicense, saveLicenseCode } from '../services/system'

const confirm = useConfirm()
const toast = useToast()

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
const activationQrDataUrl = ref('')
const activationFormRef = ref(null)

const activationPayload = computed(() => ({
  appfingerprint: license.value.appFingerprint,
  appname: license.value.appName || JPILOT_APP_NAME,
  activationdate: license.value.activationDate || new Date().toISOString()
}))

const isLicenseCodeComplete = computed(() => LICENSE_CODE_PATTERN.test(licenseCodeInput.value))

const licenseDetails = computed(() => license.value.details)

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

function displayValue(value) {
  if (value == null) return '—'
  const text = String(value).trim()
  return text ? text : '—'
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
    licenseCodeInput.value = ''
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
        licenseCodeInput.value = ''
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
    const code = license.value.details?.licenseCode
    if (code) licenseCodeInput.value = code
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

.activation-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1.25rem;
  padding-top: 0.5rem;
  border-top: 1px solid var(--p-content-border-color);
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
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(14rem, 1fr));
  gap: 1.25rem 2rem;
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
</style>
