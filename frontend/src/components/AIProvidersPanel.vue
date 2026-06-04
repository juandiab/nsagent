<template>
  <div class="content-panel content-panel-padded ai-providers-panel">
    <div class="panel-intro flex align-items-start justify-content-between gap-3 flex-wrap">
      <div>
        <div class="panel-eyebrow">
          <Tag value="LLM" severity="info" icon="pi pi-sparkles" />
          <span>Language models</span>
        </div>
        <h2 class="section-title mt-2">AI providers</h2>
        <p class="section-copy">
          Connect OpenAI, Anthropic, Gemini, Grok, DeepSeek, LM Studio, or compatible endpoints.
          Assign each model to Architect, Operator, and/or Analyst roles — use a smart model for planning
          and a faster one for operations.
        </p>
      </div>
      <div class="panel-toolbar flex align-items-center gap-2 flex-wrap">
        <IconField icon-position="left" class="search-field">
          <InputIcon class="pi pi-search" />
          <InputText v-model="searchQuery" placeholder="Search providers…" />
        </IconField>
        <Button label="Add provider" icon="pi pi-plus" size="small" @click="openCreateDialog" />
      </div>
    </div>

    <Message v-if="loadError" severity="error" :closable="false" class="mt-3">
      {{ loadError }}
    </Message>

    <DataTable
      class="ai-providers-table mt-4"
      :value="filteredProviders"
      :loading="loading"
      striped-rows
      paginator
      :rows="10"
      :rows-per-page-options="[10, 25, 50]"
      empty-message="No AI providers configured. Add one to enable JPilot."
    >
      <Column field="providerName" header="Provider Name" sortable style="min-width: 14rem">
        <template #body="{ data }">
          <div class="provider-name-cell">
            <span class="provider-name">{{ data.providerName }}</span>
            <div class="role-checkboxes">
              <label
                v-for="role in llmRoles"
                :key="role.id"
                class="role-toggle"
                v-tooltip="roleTooltip(role)"
              >
                <span
                  class="role-icon"
                  :class="{ 'role-icon-active': hasRole(data, role.id) }"
                  aria-hidden="true"
                >
                  <i :class="role.icon" />
                </span>
                <Checkbox
                  :model-value="hasRole(data, role.id)"
                  :binary="true"
                  :disabled="savingRolesId === data.id"
                  :input-id="`role-${data.id}-${role.id}`"
                  @update:model-value="(checked) => toggleRole(data, role.id, checked)"
                />
              </label>
            </div>
          </div>
        </template>
      </Column>
      <Column field="providerType" header="Type" sortable>
        <template #body="{ data }">
          <Tag :value="data.providerType" severity="info" />
        </template>
      </Column>
      <Column field="model" header="Model" sortable />
      <Column header="Status">
        <template #body="{ data }">
          <Tag
            :value="data.enabled ? 'Enabled' : 'Disabled'"
            :severity="data.enabled ? 'success' : 'secondary'"
          />
        </template>
      </Column>
      <Column header="Default">
        <template #body="{ data }">
          <Tag v-if="data.isDefault" value="Default" severity="warn" icon="pi pi-star-fill" />
        </template>
      </Column>
      <Column headerClass="actions-col" bodyClass="actions-col" style="min-width: 12rem">
        <template #header>
          <span class="actions-header">Actions</span>
        </template>
        <template #body="{ data }">
          <div class="actions-cell flex gap-1">
            <Button
              v-tooltip="tooltip('Test connection')"
              icon="pi pi-bolt"
              text
              rounded
              size="small"
              severity="info"
              :loading="testingId === data.id"
              @click="testProvider(data)"
            />
            <Button
              v-tooltip="tooltip('Edit')"
              icon="pi pi-pencil"
              text
              rounded
              size="small"
              @click="openEditDialog(data)"
            />
            <Button
              v-tooltip="tooltip('Set as default')"
              icon="pi pi-star"
              text
              rounded
              size="small"
              :disabled="data.isDefault"
              @click="setDefault(data)"
            />
            <Button
              v-tooltip="tooltip('Delete')"
              icon="pi pi-trash"
              text
              rounded
              size="small"
              severity="danger"
              @click="confirmDelete(data)"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <Dialog
      v-model:visible="dialogVisible"
      :header="isEditing ? 'Edit AI Provider' : 'Add AI Provider'"
      modal
      append-to="body"
      :style="{ width: 'min(32rem, 92vw)' }"
      :draggable="false"
      :content-style="{ overflow: 'visible' }"
    >
      <div class="flex flex-column gap-3">
        <div class="flex flex-column gap-2">
          <label for="providerName" class="field-label">Provider Name</label>
          <InputText id="providerName" v-model="form.providerName" class="w-full" />
        </div>
        <div class="flex flex-column gap-2">
          <label for="providerType" class="field-label">Provider Type</label>
          <Select
            id="providerType"
            v-model="form.providerType"
            :options="providerTypes"
            append-to="body"
            class="w-full"
            @change="onProviderTypeChange"
          />
        </div>
        <div class="flex flex-column gap-2">
          <label for="apiKey" class="field-label">API Key</label>
          <Password
            id="apiKey"
            v-model="form.apiKey"
            class="w-full"
            :feedback="false"
            toggle-mask
            input-class="w-full"
          />
          <small v-if="isEditing" class="field-hint">Leave blank to keep existing value.</small>
        </div>
        <div class="flex flex-column gap-2">
          <label for="endpoint" class="field-label">Endpoint</label>
          <InputText
            id="endpoint"
            v-model="form.endpoint"
            class="w-full"
            :placeholder="providerHint.example || 'Optional for cloud providers'"
            @blur="normalizeEndpointField"
          />
          <small class="field-hint">{{ providerHint.hostNote }}</small>
          <Message
            v-if="form.providerType === 'LM Studio'"
            severity="info"
            :closable="false"
            class="mt-2"
          >
            JPilot calls <code>POST /v1/chat/completions</code> and <code>GET /v1/models</code>.
            Opening the LM Studio server URL in a browser (e.g. port 1234) is not the web app and will log
            harmless GET / and favicon errors in LM Studio.
          </Message>
        </div>
        <div class="flex flex-column gap-2">
          <div class="flex align-items-center justify-content-between">
            <label for="model" class="field-label mb-0">Model</label>
            <Button
              label="Load models"
              icon="pi pi-refresh"
              size="small"
              text
              :loading="loadingModels"
              @click="loadModels"
            />
          </div>
          <Select
            id="model"
            v-model="form.model"
            :options="availableModels"
            append-to="body"
            class="w-full"
            placeholder="Fetch models first"
            :disabled="!availableModels.length"
            filter
            show-clear
          />
          <small class="field-hint">Select provider type, enter credentials, then load available models.</small>
        </div>
        <div class="flex align-items-center gap-2">
          <ToggleSwitch v-model="form.enabled" input-id="provider-enabled" />
          <label for="provider-enabled" class="field-label mb-0">Enabled</label>
        </div>
        <div class="flex flex-column gap-2">
          <span class="field-label">JPilot roles</span>
          <div class="role-checkboxes role-checkboxes-dialog">
            <label
              v-for="role in llmRoles"
              :key="role.id"
              class="role-toggle"
              v-tooltip="roleTooltip(role)"
            >
              <span
                class="role-icon"
                :class="{ 'role-icon-active': form.roles.includes(role.id) }"
                aria-hidden="true"
              >
                <i :class="role.icon" />
              </span>
              <Checkbox v-model="form.roles" :input-id="`form-role-${role.id}`" :value="role.id" />
            </label>
          </div>
          <small class="field-hint">Check all three to use this model for every JPilot role.</small>
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" text severity="secondary" @click="dialogVisible = false" />
        <Button
          label="Test"
          icon="pi pi-bolt"
          severity="info"
          outlined
          :loading="testingDialog"
          @click="testProviderFromDialog"
        />
        <Button label="Save" icon="pi pi-check" @click="saveProvider" :loading="saving" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'
import { getProviderHint } from '../config/aiProviders'
import { JPILOT_ROLES } from '../config/jpilotRoles'
import api from '../services/api'

const confirm = useConfirm()
const toast = useToast()

const providers = ref([])
const loading = ref(false)
const loadError = ref('')
const saving = ref(false)
const savingRolesId = ref(null)
const testingId = ref(null)
const testingDialog = ref(false)
const loadingModels = ref(false)
const availableModels = ref([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const searchQuery = ref('')

const providerTypes = ['OpenAI', 'Anthropic', 'Gemini', 'Grok', 'DeepSeek', 'LM Studio', 'OpenAI-Compatible']

const llmRoles = JPILOT_ROLES

const ALL_ROLE_IDS = JPILOT_ROLES.map((role) => role.id)

function tooltip(value) {
  return { value, appendTo: 'body', position: 'bottom' }
}

function roleTooltip(role) {
  return {
    value: role.label,
    appendTo: 'body',
    position: 'bottom'
  }
}

function normalizeRoles(roles) {
  if (!Array.isArray(roles) || !roles.length) return [...ALL_ROLE_IDS]
  return roles
}

function hasRole(provider, roleId) {
  return normalizeRoles(provider.roles).includes(roleId)
}

const emptyForm = () => ({
  providerName: '',
  providerType: 'OpenAI',
  apiKey: '',
  endpoint: '',
  model: '',
  enabled: true,
  roles: [...ALL_ROLE_IDS]
})

const form = reactive(emptyForm())

const providerHint = computed(() => getProviderHint(form.providerType))

const endpointRequired = computed(() => providerHint.value.required)

const filteredProviders = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return providers.value
  return providers.value.filter(
    (item) =>
      item.providerName.toLowerCase().includes(query) ||
      item.providerType.toLowerCase().includes(query) ||
      item.model.toLowerCase().includes(query) ||
      normalizeRoles(item.roles).some((roleId) => {
        const role = llmRoles.find((entry) => entry.id === roleId)
        return role?.label.toLowerCase().includes(query)
      })
  )
})

async function loadProviders() {
  loading.value = true
  loadError.value = ''
  try {
    const { data } = await api.get('/ai-providers')
    providers.value = Array.isArray(data) ? data : []
  } catch (error) {
    loadError.value = error.response?.data?.detail || 'Failed to load AI providers from the server'
    providers.value = []
    toast.add({ severity: 'error', summary: 'Error', detail: loadError.value, life: 5000 })
  } finally {
    loading.value = false
  }
}

function onProviderTypeChange() {
  form.model = ''
  availableModels.value = []
  if (!endpointRequired.value) {
    form.endpoint = ''
  }
}

function normalizeEndpointField() {
  if (form.providerType !== 'LM Studio') {
    return
  }
  const raw = form.endpoint.trim()
  if (!raw) {
    return
  }
  let cleaned = raw.replace(/\/+$/, '')
  cleaned = cleaned.replace(/\/(chat\/completions|models|completions)$/, '')
  cleaned = cleaned.replace(/\/api\/v1$/, '/v1')
  if (!cleaned.endsWith('/v1')) {
    try {
      const url = new URL(cleaned.includes('://') ? cleaned : `http://${cleaned}`)
      cleaned = `${url.protocol}//${url.host}/v1`
    } catch {
      return
    }
  }
  form.endpoint = cleaned
}

async function loadModels() {
  loadingModels.value = true
  try {
    let models = []
    if (isEditing.value && !form.apiKey) {
      const { data } = await api.get(`/ai-providers/${editingId.value}/models`)
      models = data.models
    } else {
      if (endpointRequired.value && !form.endpoint.trim()) {
        toast.add({
          severity: 'warn',
          summary: 'Endpoint required',
          detail: `Enter an endpoint such as ${providerHint.value.example}`,
          life: 4000
        })
        return
      }
      if (form.providerType !== 'LM Studio' && form.providerType !== 'OpenAI-Compatible' && !form.apiKey) {
        toast.add({
          severity: 'warn',
          summary: 'API key required',
          detail: 'Enter an API key to fetch models',
          life: 3000
        })
        return
      }
      const { data } = await api.post('/ai-providers/models/preview', {
        providerType: form.providerType,
        apiKey: form.apiKey,
        endpoint: form.endpoint
      })
      models = data.models
    }
    availableModels.value = models
    if (!form.model && models.length) {
      form.model = models[0]
    }
    toast.add({
      severity: 'success',
      summary: 'Models loaded',
      detail: `${models.length} model(s) available`,
      life: 2500
    })
  } catch (error) {
    const detail = error.response?.data?.detail || 'Failed to fetch models'
    toast.add({ severity: 'error', summary: 'Error', detail, life: 4000 })
  } finally {
    loadingModels.value = false
  }
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  Object.assign(form, emptyForm())
  availableModels.value = []
  dialogVisible.value = true
}

function openEditDialog(provider) {
  isEditing.value = true
  editingId.value = provider.id
  Object.assign(form, {
    providerName: provider.providerName,
    providerType: provider.providerType,
    apiKey: '',
    endpoint: provider.endpoint,
    model: provider.model,
    enabled: provider.enabled,
    roles: [...normalizeRoles(provider.roles)]
  })
  availableModels.value = provider.model ? [provider.model] : []
  dialogVisible.value = true
  loadModels()
}

function buildPayload() {
  const payload = {
    providerName: form.providerName,
    providerType: form.providerType,
    endpoint: form.endpoint,
    model: form.model,
    enabled: form.enabled,
    roles: [...form.roles]
  }

  if (!isEditing.value) {
    payload.apiKey = form.apiKey
  } else if (form.apiKey) {
    payload.apiKey = form.apiKey
  }

  return payload
}

async function saveProvider() {
  saving.value = true
  try {
    if (!form.roles.length) {
      toast.add({
        severity: 'warn',
        summary: 'Role required',
        detail: 'Select at least one JPilot role for this provider',
        life: 3500
      })
      return
    }
    const payload = buildPayload()
    if (isEditing.value) {
      await api.put(`/ai-providers/${editingId.value}`, payload)
      toast.add({ severity: 'success', summary: 'Updated', detail: 'AI provider updated', life: 3000 })
    } else {
      await api.post('/ai-providers', payload)
      toast.add({ severity: 'success', summary: 'Created', detail: 'AI provider created', life: 3000 })
    }
    dialogVisible.value = false
    await loadProviders()
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to save AI provider', life: 3000 })
  } finally {
    saving.value = false
  }
}

async function testProvider(provider) {
  testingId.value = provider.id
  try {
    const { data } = await api.post(`/ai-providers/${provider.id}/test`)
    toast.add({
      severity: data.success ? 'success' : 'error',
      summary: data.success ? 'Connection OK' : 'Connection failed',
      detail: data.message,
      life: 5000
    })
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to test provider', life: 3000 })
  } finally {
    testingId.value = null
  }
}

async function testProviderFromDialog() {
  testingDialog.value = true
  try {
    let response
    if (isEditing.value && !form.apiKey) {
      response = await api.post(`/ai-providers/${editingId.value}/test`)
    } else {
      if (endpointRequired.value && !form.endpoint.trim()) {
        toast.add({
          severity: 'warn',
          summary: 'Endpoint required',
          detail: `Enter an endpoint such as ${providerHint.value.example}`,
          life: 4000
        })
        return
      }
      response = await api.post('/ai-providers/test/preview', {
        providerType: form.providerType,
        apiKey: form.apiKey,
        endpoint: form.endpoint,
        model: form.model
      })
    }
    toast.add({
      severity: response.data.success ? 'success' : 'error',
      summary: response.data.success ? 'Connection OK' : 'Connection failed',
      detail: response.data.message,
      life: 5000
    })
  } catch (error) {
    const detail = error.response?.data?.detail || 'Failed to test provider'
    toast.add({ severity: 'error', summary: 'Error', detail, life: 4000 })
  } finally {
    testingDialog.value = false
  }
}

async function toggleRole(provider, roleId, checked) {
  const currentRoles = normalizeRoles(provider.roles)
  const nextRoles = checked
    ? [...new Set([...currentRoles, roleId])]
    : currentRoles.filter((role) => role !== roleId)

  if (!nextRoles.length) {
    toast.add({
      severity: 'warn',
      summary: 'Role required',
      detail: 'Each provider must be assigned to at least one role',
      life: 3500
    })
    return
  }

  savingRolesId.value = provider.id
  try {
    await api.put(`/ai-providers/${provider.id}`, { roles: nextRoles })
    provider.roles = nextRoles
    toast.add({
      severity: 'success',
      summary: 'Roles updated',
      detail: `${provider.providerName} role assignment saved`,
      life: 2500
    })
  } catch (error) {
    const detail = error.response?.data?.detail || 'Failed to update provider roles'
    toast.add({ severity: 'error', summary: 'Error', detail, life: 4000 })
  } finally {
    savingRolesId.value = null
  }
}

async function setDefault(provider) {
  try {
    await api.patch(`/ai-providers/${provider.id}/set-default`)
    toast.add({
      severity: 'success',
      summary: 'Default set',
      detail: `${provider.providerName} is now default`,
      life: 3000
    })
    await loadProviders()
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to set default provider', life: 3000 })
  }
}

function confirmDelete(provider) {
  confirm.require({
    message: `Delete "${provider.providerName}"? This action cannot be undone.`,
    header: 'Confirm Delete',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await api.delete(`/ai-providers/${provider.id}`)
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'AI provider deleted', life: 3000 })
        await loadProviders()
      } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete AI provider', life: 3000 })
      }
    }
  })
}

onMounted(loadProviders)
</script>

<style scoped>
.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.section-copy {
  margin: 0.35rem 0 0;
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
  max-width: 42rem;
}

.panel-eyebrow {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--p-text-muted-color);
}

.panel-toolbar {
  flex-shrink: 0;
}

.search-field {
  min-width: 12rem;
}

.field-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--p-text-color);
}

.field-hint {
  color: var(--p-text-muted-color);
  font-size: 0.8125rem;
}

.ai-providers-panel {
  overflow: visible;
}

.ai-providers-table :deep(.actions-col) {
  width: 12rem;
  min-width: 12rem;
}

.ai-providers-table :deep(thead .actions-col) {
  pointer-events: none;
}

.ai-providers-table :deep(tbody .actions-col) {
  position: relative;
  z-index: 1;
}

.actions-cell {
  min-height: 2rem;
  align-items: center;
}

.provider-name-cell {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.provider-name {
  font-weight: 500;
}

.role-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 0.75rem;
}

.role-checkboxes-dialog {
  gap: 0.75rem 1.25rem;
}

.role-toggle {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  cursor: pointer;
  user-select: none;
}

.role-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.65rem;
  height: 1.65rem;
  border-radius: 0.375rem;
  color: var(--p-text-muted-color);
  opacity: 0.45;
  transition: color 0.15s ease, opacity 0.15s ease, background-color 0.15s ease;
}

.role-icon i {
  font-size: 0.95rem;
}

.role-icon-active {
  color: var(--p-primary-color);
  opacity: 1;
  background: color-mix(in srgb, var(--p-primary-color) 12%, transparent);
}

.role-toggle:hover .role-icon {
  opacity: 0.85;
}

.role-toggle:hover .role-icon-active {
  opacity: 1;
}

.role-toggle :deep(.p-checkbox) {
  width: 1rem;
  height: 1rem;
}

.role-toggle :deep(.p-checkbox-box) {
  width: 1rem;
  height: 1rem;
}
</style>
