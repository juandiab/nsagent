<template>
  <div class="content-panel content-panel-padded">
    <div class="flex align-items-start justify-content-between gap-3 flex-wrap">
      <div>
        <h2 class="section-title">JPilot HTTPS certificate</h2>
        <p class="section-copy m-0">
          TLS for the JPilot web UI is terminated by nginx
          <template v-if="status.hostname"> at <code>https://{{ status.hostname }}</code></template>.
        </p>
      </div>
      <Tag
        v-if="!statusLoading && status.has_certificate"
        value="Active"
        severity="success"
        icon="pi pi-lock"
      />
    </div>

    <div v-if="statusLoading" class="mt-4">
      <ProgressSpinner style="width: 2rem; height: 2rem" />
    </div>

    <div v-else class="flex flex-column gap-4 mt-4">
      <Message v-if="!status.available" severity="warn" :closable="false">
        {{ status.message || 'TLS management is not available from the API container. Replace files under nginx/ssl/ on the host instead.' }}
      </Message>

      <template v-if="!replacing">
        <div v-if="status.has_certificate" class="tls-status-grid">
          <div>
            <div class="setting-label">Public hostname</div>
            <div class="setting-hint">{{ status.hostname || '—' }}</div>
          </div>
          <div>
            <div class="setting-label">Certificate</div>
            <div class="setting-hint">
              {{ status.common_name || '—' }}
              <template v-if="status.expires">
                — expires {{ status.expires }}
                <template v-if="status.expires_in_days != null">({{ status.expires_in_days }} days)</template>
              </template>
            </div>
          </div>
        </div>

        <Message v-else severity="info" :closable="false">
          No certificate is installed yet. Use replace to upload one.
        </Message>

        <div v-if="status.available" class="flex gap-2 flex-wrap">
          <Button
            label="Replace certificate"
            icon="pi pi-sync"
            size="small"
            severity="secondary"
            outlined
            @click="startReplace"
          />
        </div>

        <Message v-if="actionMessage && !replacing" :severity="actionSeverity" :closable="false">
          {{ actionMessage }}
        </Message>
      </template>

      <template v-else>
        <p class="section-copy m-0">
          Drop, browse, or paste PEM files, then validate and apply. Existing files are backed up as
          <code>cert.crt.bak</code> and <code>cert.key.bak</code>.
        </p>

        <div
          class="tls-drop-zone setting-row"
          :class="{ 'is-dragover': dragOverField === 'certificate' }"
          @dragenter.prevent="setDragOver('certificate')"
          @dragover.prevent="setDragOver('certificate')"
          @dragleave.prevent="clearDragOver('certificate', $event)"
          @drop.prevent="onDropFiles($event, 'certificate')"
        >
          <div class="flex align-items-center justify-content-between gap-2 flex-wrap">
            <label for="tlsCertificate" class="setting-label m-0">Certificate (PEM)</label>
            <Button
              label="Browse file"
              icon="pi pi-folder-open"
              size="small"
              severity="secondary"
              text
              :disabled="applying"
              @click="certificateFileInput?.click()"
            />
          </div>
          <input
            ref="certificateFileInput"
            type="file"
            class="tls-file-input"
            accept=".pem,.crt,.cer,.txt,.key,text/plain"
            :disabled="applying"
            @change="onPickFiles($event, 'certificate')"
          />
          <Textarea
            id="tlsCertificate"
            v-model="form.certificate"
            rows="8"
            class="w-full font-mono text-sm"
            placeholder="-----BEGIN CERTIFICATE-----"
            :disabled="applying"
            @input="clearValidation"
          />
          <small class="setting-hint">Drop a <code>.crt</code> / <code>.pem</code> file here or paste below.</small>
        </div>

        <div
          class="tls-drop-zone setting-row"
          :class="{ 'is-dragover': dragOverField === 'privateKey' }"
          @dragenter.prevent="setDragOver('privateKey')"
          @dragover.prevent="setDragOver('privateKey')"
          @dragleave.prevent="clearDragOver('privateKey', $event)"
          @drop.prevent="onDropFiles($event, 'privateKey')"
        >
          <div class="flex align-items-center justify-content-between gap-2 flex-wrap">
            <label for="tlsPrivateKey" class="setting-label m-0">Private key (PEM)</label>
            <Button
              label="Browse file"
              icon="pi pi-folder-open"
              size="small"
              severity="secondary"
              text
              :disabled="applying"
              @click="privateKeyFileInput?.click()"
            />
          </div>
          <input
            ref="privateKeyFileInput"
            type="file"
            class="tls-file-input"
            accept=".pem,.key,.txt,text/plain"
            :disabled="applying"
            @change="onPickFiles($event, 'privateKey')"
          />
          <Textarea
            id="tlsPrivateKey"
            v-model="form.privateKey"
            rows="8"
            class="w-full font-mono text-sm"
            placeholder="-----BEGIN PRIVATE KEY-----"
            :disabled="applying"
            @input="clearValidation"
          />
          <small class="setting-hint">
            Drop a <code>.key</code> / <code>.pem</code> file here or paste below. Unencrypted PEM only;
            the key is sent over HTTPS and is never stored in the browser.
          </small>
        </div>

        <div
          class="tls-drop-zone setting-row"
          :class="{ 'is-dragover': dragOverField === 'chain' }"
          @dragenter.prevent="setDragOver('chain')"
          @dragover.prevent="setDragOver('chain')"
          @dragleave.prevent="clearDragOver('chain', $event)"
          @drop.prevent="onDropFiles($event, 'chain')"
        >
          <div class="flex align-items-center justify-content-between gap-2 flex-wrap">
            <label for="tlsChain" class="setting-label m-0">Intermediate chain (optional PEM)</label>
            <Button
              label="Browse file"
              icon="pi pi-folder-open"
              size="small"
              severity="secondary"
              text
              :disabled="applying"
              @click="chainFileInput?.click()"
            />
          </div>
          <input
            ref="chainFileInput"
            type="file"
            class="tls-file-input"
            accept=".pem,.crt,.cer,.txt,text/plain"
            multiple
            :disabled="applying"
            @change="onPickFiles($event, 'chain')"
          />
          <Textarea
            id="tlsChain"
            v-model="form.chain"
            rows="5"
            class="w-full font-mono text-sm"
            placeholder="-----BEGIN CERTIFICATE----- (intermediate CA)"
            :disabled="applying"
            @input="clearValidation"
          />
          <small class="setting-hint">Drop intermediate CA bundle files here. Multiple certificates are appended automatically.</small>
        </div>

        <Message v-if="dropMessage" :severity="dropMessageSeverity" :closable="false">
          {{ dropMessage }}
        </Message>

        <div class="flex gap-2 flex-wrap">
          <Button
            label="Validate certificate"
            icon="pi pi-check-circle"
            size="small"
            severity="secondary"
            outlined
            :loading="validating"
            :disabled="!canValidate"
            @click="validateCertificate"
          />
          <Button
            label="Apply replacement"
            icon="pi pi-sync"
            size="small"
            :loading="applying"
            :disabled="!validation.ok"
            @click="confirmApply"
          />
          <Button
            label="Cancel"
            icon="pi pi-times"
            size="small"
            severity="secondary"
            text
            :disabled="applying || validating"
            @click="cancelReplace"
          />
        </div>

        <Message v-if="validation.message" :severity="validation.severity" :closable="false">
          {{ validation.message }}
        </Message>
        <Message v-if="actionMessage" :severity="actionSeverity" :closable="false">
          {{ actionMessage }}
        </Message>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import Button from 'primevue/button'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import {
  applyTlsCertificate,
  getTlsCertificateStatus,
  validateTlsCertificate
} from '../services/security'

const statusLoading = ref(true)
const replacing = ref(false)
const validating = ref(false)
const applying = ref(false)
const actionMessage = ref('')
const actionSeverity = ref('info')
const dropMessage = ref('')
const dropMessageSeverity = ref('info')
const dragOverField = ref(null)
const certificateFileInput = ref(null)
const privateKeyFileInput = ref(null)
const chainFileInput = ref(null)

const PEM_CERT_RE = /-----BEGIN CERTIFICATE-----/
const PEM_KEY_RE = /-----BEGIN (?:RSA |EC )?PRIVATE KEY-----/
const PEM_CERT_BLOCK_RE = /-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----/g

const status = reactive({
  available: false,
  hostname: '',
  has_certificate: false,
  common_name: '',
  expires: '',
  expires_in_days: null,
  message: ''
})

const form = reactive({
  certificate: '',
  privateKey: '',
  chain: ''
})

const validation = reactive({
  ok: false,
  message: '',
  severity: 'info'
})

const canValidate = computed(
  () => form.certificate.trim().length > 0 && form.privateKey.trim().length > 0
)

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error(`Could not read ${file.name}`))
    reader.readAsText(file)
  })
}

function splitCertificateBlocks(text) {
  return text.match(PEM_CERT_BLOCK_RE) || []
}

function classifyPem(text) {
  const trimmed = text.trim()
  const hasCert = PEM_CERT_RE.test(trimmed)
  const hasKey = PEM_KEY_RE.test(trimmed)
  if (hasKey && !hasCert) return 'privateKey'
  if (hasCert && !hasKey) return 'certificate'
  if (hasCert && hasKey) return 'mixed'
  return 'unknown'
}

function appendChain(text) {
  const blocks = splitCertificateBlocks(text)
  const next = (blocks.length ? blocks : [text.trim()]).join('\n')
  form.chain = form.chain.trim() ? `${form.chain.trim()}\n${next}` : next
}

function setFormField(field, text) {
  if (field === 'certificate') form.certificate = text.trim()
  else if (field === 'privateKey') form.privateKey = text.trim()
  else appendChain(text)
  clearValidation()
}

function resolveTargetField(kind, preferredField) {
  if (kind === 'certificate' || kind === 'privateKey') return kind
  if (kind === 'mixed') return preferredField
  return preferredField
}

function ingestPemText(text, preferredField, fileName = '') {
  const kind = classifyPem(text)

  if (kind === 'unknown') {
    dropMessageSeverity.value = 'warn'
    dropMessage.value = fileName
      ? `${fileName} does not look like a PEM certificate or private key.`
      : 'Dropped content does not look like a PEM certificate or private key.'
    return false
  }

  if (preferredField === 'chain') {
    if (kind === 'privateKey') {
      setFormField('privateKey', text)
      dropMessageSeverity.value = 'info'
      dropMessage.value = fileName
        ? `${fileName} looks like a private key — placed in the private key field.`
        : 'Placed the private key in the matching field.'
      return true
    }
    appendChain(text)
    dropMessage.value = ''
    return true
  }

  const target = resolveTargetField(kind, preferredField)

  if (target !== preferredField && kind !== 'mixed') {
    dropMessageSeverity.value = 'info'
    dropMessage.value = fileName
      ? `${fileName} looks like a ${kind === 'privateKey' ? 'private key' : 'certificate'} — placed in the matching field.`
      : `Placed the ${kind === 'privateKey' ? 'private key' : 'certificate'} in the matching field.`
  } else {
    dropMessage.value = ''
  }

  if (target === 'certificate') {
    const blocks = splitCertificateBlocks(text)
    if (blocks.length > 1) {
      setFormField('certificate', blocks[0])
      appendChain(blocks.slice(1).join('\n'))
      if (!dropMessage.value) {
        dropMessageSeverity.value = 'info'
        dropMessage.value = 'Multiple certificates detected — leaf cert and intermediates were split automatically.'
      }
      return true
    }
  }

  setFormField(target, text)
  return true
}

function setDragOver(field) {
  if (applying.value) return
  dragOverField.value = field
}

function clearDragOver(field, event) {
  if (event.currentTarget?.contains(event.relatedTarget)) return
  if (dragOverField.value === field) dragOverField.value = null
}

async function loadFilesIntoForm(files, preferredField) {
  const list = [...files].filter((file) => file && file.size > 0)
  if (!list.length) return

  dropMessage.value = ''
  let loaded = 0
  for (const file of list) {
    try {
      const text = await readFileAsText(file)
      if (ingestPemText(text, preferredField, file.name)) loaded += 1
    } catch (error) {
      dropMessageSeverity.value = 'error'
      dropMessage.value = error.message || `Could not read ${file.name}.`
    }
  }

  if (loaded > 1 && !dropMessage.value) {
    dropMessageSeverity.value = 'success'
    dropMessage.value = `Loaded ${loaded} files.`
  }
}

async function onDropFiles(event, preferredField) {
  dragOverField.value = null
  if (applying.value) return
  await loadFilesIntoForm(event.dataTransfer?.files || [], preferredField)
}

async function onPickFiles(event, preferredField) {
  const input = event.target
  await loadFilesIntoForm(input?.files || [], preferredField)
  if (input) input.value = ''
}

function resetForm() {
  form.certificate = ''
  form.privateKey = ''
  form.chain = ''
  validation.ok = false
  validation.message = ''
  dropMessage.value = ''
}

function clearValidation() {
  validation.ok = false
  validation.message = ''
  actionMessage.value = ''
}

function startReplace() {
  resetForm()
  actionMessage.value = ''
  replacing.value = true
}

function cancelReplace() {
  resetForm()
  actionMessage.value = ''
  replacing.value = false
}

function payload() {
  return {
    certificate: form.certificate,
    private_key: form.privateKey,
    chain: form.chain
  }
}

async function loadStatus() {
  statusLoading.value = true
  try {
    const data = await getTlsCertificateStatus()
    Object.assign(status, data)
  } catch (error) {
    status.available = false
    status.message = error.response?.data?.detail || error.message || 'Could not load TLS status.'
  } finally {
    statusLoading.value = false
  }
}

async function validateCertificate() {
  validating.value = true
  validation.ok = false
  validation.message = ''
  try {
    const data = await validateTlsCertificate(payload())
    if (data.ok) {
      validation.ok = true
      validation.severity = 'success'
      validation.message = `Valid for ${data.common_name || '(no CN)'} — expires ${data.expires} (${data.expires_in_days} days). Hostname ${data.hostname} is covered.`
    } else {
      validation.severity = 'error'
      validation.message = data.error || 'Validation failed.'
    }
  } catch (error) {
    validation.severity = 'error'
    validation.message = error.response?.data?.detail || error.message || 'Validation request failed.'
  } finally {
    validating.value = false
  }
}

async function confirmApply() {
  if (!validation.ok) return
  if (!window.confirm('Replace the JPilot HTTPS certificate and reload nginx?')) return
  applying.value = true
  actionMessage.value = ''
  try {
    const data = await applyTlsCertificate(payload())
    if (data.ok) {
      actionSeverity.value = 'success'
      actionMessage.value = data.message || 'Certificate replaced.'
      resetForm()
      replacing.value = false
      await loadStatus()
    } else {
      actionSeverity.value = 'error'
      actionMessage.value = data.error || 'Could not replace certificate.'
    }
  } catch (error) {
    actionSeverity.value = 'error'
    actionMessage.value = error.response?.data?.detail || error.message || 'Replace request failed.'
  } finally {
    applying.value = false
  }
}

onMounted(loadStatus)
</script>

<style scoped>
.tls-status-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr));
}

.font-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.tls-file-input {
  display: none;
}

.tls-drop-zone {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 1px dashed transparent;
  border-radius: var(--p-content-border-radius, 8px);
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.tls-drop-zone.is-dragover {
  border-color: var(--p-primary-color, #3b82f6);
  background: color-mix(in srgb, var(--p-primary-color, #3b82f6) 8%, transparent);
}
</style>
