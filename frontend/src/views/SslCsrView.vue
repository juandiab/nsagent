<template>
  <div class="page">
    <PageHeader
      title="SSL Certificate Tools"
      subtitle="Generate a CSR for a CA or a self-signed certificate directly on your NetScaler"
    />

    <div class="grid">
      <div class="col-12 xl:col-5">
        <div class="content-panel content-panel-padded">
          <form class="flex flex-column gap-4" @submit.prevent="submit">
            <div class="flex flex-column gap-2">
              <label for="appliance" class="field-label">NetScaler</label>
              <Select
                id="appliance"
                v-model="form.applianceId"
                :options="applianceOptions"
                option-label="label"
                option-value="value"
                placeholder="Select appliance"
                :loading="loadingAppliances"
                class="w-full"
              />
            </div>

            <div class="flex flex-column gap-2">
              <label for="generationMode" class="field-label">Generate</label>
              <Select
                id="generationMode"
                v-model="form.generationMode"
                :options="generationModeOptions"
                option-label="label"
                option-value="value"
                class="w-full"
              />
              <small class="field-hint">{{ generationModeHint }}</small>
            </div>

            <div class="flex flex-column gap-2">
              <label for="keyName" class="field-label">Key name</label>
              <InputText
                id="keyName"
                v-model="form.keyName"
                placeholder="e.g. storefront_prod"
                class="w-full"
              />
              <small class="field-hint">{{ keyNameHint }}</small>
            </div>

            <div class="grid">
              <div class="col-12 md:col-6 flex flex-column gap-2">
                <label for="certType" class="field-label">Certificate type</label>
                <Select
                  id="certType"
                  v-model="form.certType"
                  :options="certTypeOptions"
                  option-label="label"
                  option-value="value"
                  class="w-full"
                  @change="onCertTypeChange"
                />
              </div>
              <div class="col-12 md:col-6 flex flex-column gap-2">
                <label for="keyType" class="field-label">Key algorithm</label>
                <Select
                  id="keyType"
                  v-model="form.keyType"
                  :options="keyTypeOptions"
                  option-label="label"
                  option-value="value"
                  class="w-full"
                />
              </div>
            </div>

            <div v-if="form.keyType === 'rsa'" class="flex flex-column gap-2">
              <label for="keySize" class="field-label">RSA key size</label>
              <Select
                id="keySize"
                v-model="form.keySize"
                :options="keySizeOptions"
                option-label="label"
                option-value="value"
                class="w-full"
              />
            </div>

            <div v-if="form.generationMode === 'self_signed'" class="flex flex-column gap-2">
              <label for="validityDays" class="field-label">Validity (days)</label>
              <InputNumber
                id="validityDays"
                v-model="form.validityDays"
                :min="1"
                :max="3650"
                show-buttons
                class="w-full"
              />
            </div>

            <div class="flex flex-column gap-2">
              <label for="keyPassword" class="field-label">Key password (optional)</label>
              <Password
                id="keyPassword"
                v-model="form.keyPassword"
                :feedback="false"
                toggle-mask
                class="w-full"
                input-class="w-full"
                placeholder="Encrypt private key on appliance"
              />
            </div>

            <Divider />

            <div class="flex flex-column gap-2">
              <label for="commonName" class="field-label">Common name (CN)</label>
              <InputText
                id="commonName"
                v-model="form.commonName"
                :placeholder="cnPlaceholder"
                class="w-full"
              />
            </div>

            <div v-if="form.certType === 'san'" class="flex flex-column gap-2">
              <label for="sans" class="field-label">Subject Alternative Names</label>
              <Textarea
                id="sans"
                v-model="form.subjectAltNamesText"
                rows="4"
                auto-resize
                class="w-full"
                placeholder="One DNS name or IP per line&#10;www.example.com&#10;api.example.com"
              />
            </div>

            <div class="grid">
              <div class="col-12 md:col-4 flex flex-column gap-2">
                <label for="country" class="field-label">Country</label>
                <InputText id="country" v-model="form.country" maxlength="2" class="w-full" />
              </div>
              <div class="col-12 md:col-8 flex flex-column gap-2">
                <label for="state" class="field-label">
                  State / Province
                  <span v-if="form.generationMode === 'self_signed'" class="field-required">*</span>
                </label>
                <InputText
                  id="state"
                  v-model="form.state"
                  class="w-full"
                  :placeholder="form.generationMode === 'self_signed' ? 'Required for NetScaler (e.g. CA or NA)' : ''"
                />
              </div>
            </div>

            <div class="grid">
              <div class="col-12 md:col-6 flex flex-column gap-2">
                <label for="locality" class="field-label">Locality</label>
                <InputText id="locality" v-model="form.locality" class="w-full" />
              </div>
              <div class="col-12 md:col-6 flex flex-column gap-2">
                <label for="organization" class="field-label">
                  Organization
                  <span v-if="form.generationMode === 'self_signed'" class="field-required">*</span>
                </label>
                <InputText
                  id="organization"
                  v-model="form.organization"
                  class="w-full"
                  :placeholder="form.generationMode === 'self_signed' ? 'Required for NetScaler' : ''"
                />
              </div>
            </div>

            <div class="grid">
              <div class="col-12 md:col-6 flex flex-column gap-2">
                <label for="ou" class="field-label">Organizational unit</label>
                <InputText id="ou" v-model="form.organizationalUnit" class="w-full" />
              </div>
              <div class="col-12 md:col-6 flex flex-column gap-2">
                <label for="email" class="field-label">Email</label>
                <InputText id="email" v-model="form.email" type="email" class="w-full" />
              </div>
            </div>

            <Message v-if="errorMessage" severity="error" :closable="false">{{ errorMessage }}</Message>
            <Message v-if="successMessage" severity="success" :closable="false">{{ successMessage }}</Message>

            <div class="flex gap-2">
              <Button
                type="submit"
                :label="submitLabel"
                icon="pi pi-key"
                :loading="submitting"
                :disabled="!canSubmit"
              />
              <Button
                type="button"
                label="Reset"
                severity="secondary"
                outlined
                :disabled="submitting"
                @click="resetForm"
              />
            </div>
          </form>
        </div>
      </div>

      <div class="col-12 xl:col-7">
        <div class="content-panel content-panel-padded">
          <CsrTerminal
            :title="terminalTitle"
            :copy-label="terminalCopyLabel"
            :pem="result.pem"
            :key-path="result.keyPath"
            :csr-path="result.csrPath"
            :cert-path="result.certPath"
            :req-path="result.reqPath"
            :cert-key-name="result.certKeyName"
            :placeholder="terminalPlaceholder"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import Button from 'primevue/button'
import Divider from 'primevue/divider'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import PageHeader from '../components/PageHeader.vue'
import CsrTerminal from '../components/CsrTerminal.vue'
import api from '../services/api'
import { generateSslCsr } from '../services/sslCsr'

const loadingAppliances = ref(true)
const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const appliances = ref([])

const form = reactive({
  applianceId: '',
  generationMode: 'csr',
  keyName: '',
  certType: 'standard',
  keyType: 'rsa',
  keySize: 2048,
  validityDays: 365,
  keyPassword: '',
  commonName: '',
  country: 'US',
  state: '',
  locality: '',
  organization: '',
  organizationalUnit: '',
  email: '',
  subjectAltNamesText: ''
})

const result = reactive({
  pem: '',
  keyPath: '',
  csrPath: '',
  certPath: '',
  reqPath: '',
  certKeyName: ''
})

const generationModeOptions = [
  { label: 'Certificate signing request (CSR)', value: 'csr' },
  { label: 'Self-signed certificate', value: 'self_signed' }
]

const certTypeOptions = [
  { label: 'Standard', value: 'standard' },
  { label: 'Wildcard', value: 'wildcard' },
  { label: 'SAN (multi-name)', value: 'san' }
]

const keyTypeOptions = [
  { label: 'RSA', value: 'rsa' },
  { label: 'ECDSA (P-256)', value: 'ecdsa' }
]

const keySizeOptions = [
  { label: '2048 bits', value: 2048 },
  { label: '3072 bits', value: 3072 },
  { label: '4096 bits', value: 4096 }
]

const applianceOptions = computed(() =>
  appliances.value
    .filter((item) => item.enabled)
    .map((item) => ({ label: item.name, value: item.id }))
)

const cnPlaceholder = computed(() => {
  if (form.certType === 'wildcard') return '*.example.com'
  return 'www.example.com'
})

const generationModeHint = computed(() =>
  form.generationMode === 'self_signed'
    ? 'Uses NetScaler CLI: create ssl rsakey, certReq, and cert ROOT_CERT in /nsconfig/ssl.'
    : 'Uses OpenSSL on the appliance shell to create a CSR you can submit to your CA.'
)

const keyNameHint = computed(() =>
  form.generationMode === 'self_signed'
    ? 'Creates key, CSR, cert, and certKey on the appliance. certKey name matches this field (bind with bind ssl vserver).'
    : 'Creates /nsconfig/ssl/<name>.key and /nsconfig/ssl/<name>.csr on the appliance.'
)

const submitLabel = computed(() =>
  form.generationMode === 'self_signed' ? 'Generate self-signed certificate' : 'Generate CSR'
)

const terminalTitle = computed(() =>
  form.generationMode === 'self_signed' ? 'Self-signed certificate' : 'Certificate signing request'
)

const terminalCopyLabel = computed(() =>
  form.generationMode === 'self_signed' ? 'Copy certificate' : 'Copy CSR'
)

const terminalPlaceholder = computed(() =>
  form.generationMode === 'self_signed'
    ? 'The self-signed certificate PEM will appear here after generation.'
    : 'The CSR PEM will appear here after generation.'
)

const canSubmit = computed(() => {
  const base = Boolean(form.applianceId && form.keyName.trim() && form.commonName.trim() && !submitting.value)
  if (!base) return false
  if (form.generationMode === 'self_signed') {
    return Boolean(form.state.trim() && form.organization.trim())
  }
  return true
})

function parseSans(text) {
  return text
    .split(/[\n,]+/)
    .map((entry) => entry.trim())
    .filter(Boolean)
}

function onCertTypeChange() {
  if (form.certType === 'wildcard' && form.commonName && !form.commonName.startsWith('*.')) {
    form.commonName = `*.${form.commonName.replace(/^\*\./, '')}`
  }
}

function resetForm() {
  form.generationMode = 'csr'
  form.keyName = ''
  form.certType = 'standard'
  form.keyType = 'rsa'
  form.keySize = 2048
  form.validityDays = 365
  form.keyPassword = ''
  form.commonName = ''
  form.country = 'US'
  form.state = ''
  form.locality = ''
  form.organization = ''
  form.organizationalUnit = ''
  form.email = ''
  form.subjectAltNamesText = ''
  result.pem = ''
  result.keyPath = ''
  result.csrPath = ''
  result.certPath = ''
  result.reqPath = ''
  result.certKeyName = ''
  errorMessage.value = ''
  successMessage.value = ''
}

async function loadAppliances() {
  loadingAppliances.value = true
  try {
    const { data } = await api.get('/appliances')
    appliances.value = data
    if (!form.applianceId && data.length) {
      const enabled = data.find((item) => item.enabled)
      form.applianceId = enabled?.id || data[0].id
    }
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Failed to load NetScalers'
  } finally {
    loadingAppliances.value = false
  }
}

async function submit() {
  errorMessage.value = ''
  successMessage.value = ''
  submitting.value = true

  try {
    const payload = {
      appliance_id: form.applianceId,
      generation_mode: form.generationMode,
      key_name: form.keyName.trim(),
      cert_type: form.certType,
      key_type: form.keyType,
      key_size: form.keySize,
      validity_days: form.validityDays,
      key_password: form.keyPassword || null,
      common_name: form.commonName.trim(),
      country: form.country.trim().toUpperCase(),
      state: form.state.trim(),
      locality: form.locality.trim(),
      organization: form.organization.trim(),
      organizational_unit: form.organizationalUnit.trim(),
      email: form.email.trim() || null,
      subject_alt_names: form.certType === 'san' ? parseSans(form.subjectAltNamesText) : []
    }

    const data = await generateSslCsr(payload)
    result.pem = data.generation_mode === 'self_signed' ? data.certificate : data.csr
    result.keyPath = data.key_path
    result.csrPath = data.csr_path
    result.certPath = data.cert_path
    result.reqPath = data.req_path
    result.certKeyName = data.cert_key_name || ''
    successMessage.value =
      data.message ||
      (data.generation_mode === 'self_signed'
        ? 'Self-signed certificate created on the NetScaler.'
        : 'CSR generated on the NetScaler. Copy the PEM below and submit it to your CA.')
  } catch (error) {
    result.pem = ''
    result.keyPath = ''
    result.csrPath = ''
    result.certPath = ''
    result.reqPath = ''
    result.certKeyName = ''
    errorMessage.value =
      error.response?.data?.detail || error.message || 'SSL generation failed'
  } finally {
    submitting.value = false
  }
}

onMounted(loadAppliances)
</script>

<style scoped>
.field-label {
  font-size: 0.875rem;
  font-weight: 600;
}

.field-hint {
  color: var(--p-text-muted-color);
}

.field-required {
  color: var(--p-orange-500);
  margin-left: 0.15rem;
}
</style>
