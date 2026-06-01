<template>
  <div class="page">
    <PageHeader
      title="AI Providers"
      subtitle="Configure LLM providers for intelligent automation"
      searchable
      v-model:search="searchQuery"
    >
      <template #actions>
        <Button label="Add Provider" icon="pi pi-plus" size="small" @click="openCreateDialog" />
      </template>
    </PageHeader>

    <AiSectionNav />

    <div class="content-panel">
      <DataTable
        :value="filteredProviders"
        :loading="loading"
        striped-rows
        paginator
        :rows="10"
        :rows-per-page-options="[10, 25, 50]"
        empty-message="No AI providers configured. Add one to enable intelligent features."
      >
        <Column field="providerName" header="Provider Name" sortable />
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
        <Column header="Actions" style="min-width: 10rem">
          <template #body="{ data }">
            <div class="flex gap-1">
              <Button
                v-tooltip.top="'Test connection'"
                icon="pi pi-bolt"
                text
                rounded
                size="small"
                severity="info"
                :loading="testingId === data.id"
                @click="testProvider(data)"
              />
              <Button
                v-tooltip.top="'Edit'"
                icon="pi pi-pencil"
                text
                rounded
                size="small"
                @click="openEditDialog(data)"
              />
              <Button
                v-tooltip.top="'Set as default'"
                icon="pi pi-star"
                text
                rounded
                size="small"
                :disabled="data.isDefault"
                @click="setDefault(data)"
              />
              <Button
                v-tooltip.top="'Delete'"
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
    </div>

    <Dialog
      v-model:visible="dialogVisible"
      :header="isEditing ? 'Edit AI Provider' : 'Add AI Provider'"
      modal
      :style="{ width: 'min(32rem, 92vw)' }"
      :draggable="false"
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
            Copilot calls <code>POST /v1/chat/completions</code> and <code>GET /v1/models</code>.
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
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'
import PageHeader from '../components/PageHeader.vue'
import AiSectionNav from '../components/AiSectionNav.vue'
import { getProviderHint } from '../config/aiProviders'
import api from '../services/api'

const confirm = useConfirm()
const toast = useToast()

const providers = ref([])
const loading = ref(false)
const saving = ref(false)
const testingId = ref(null)
const testingDialog = ref(false)
const loadingModels = ref(false)
const availableModels = ref([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const searchQuery = ref('')

const providerTypes = ['OpenAI', 'Anthropic', 'Gemini', 'Grok', 'LM Studio', 'OpenAI-Compatible']

const emptyForm = () => ({
  providerName: '',
  providerType: 'OpenAI',
  apiKey: '',
  endpoint: '',
  model: '',
  enabled: true
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
      item.model.toLowerCase().includes(query)
  )
})

async function loadProviders() {
  loading.value = true
  try {
    const { data } = await api.get('/ai-providers')
    providers.value = data
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load AI providers', life: 3000 })
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
    enabled: provider.enabled
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
    enabled: form.enabled
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
.page {
  animation: page-in 0.35s ease;
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
