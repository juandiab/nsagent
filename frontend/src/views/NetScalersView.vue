<template>
  <div class="page">
    <PageHeader
      title="NetScalers"
      :subtitle="headerSubtitle"
      :searchable="activeTab === 'inventory'"
      v-model:search="searchQuery"
    >
      <template v-if="activeTab === 'inventory'" #actions>
        <Button label="Add NetScaler" icon="pi pi-plus" size="small" @click="openCreateDialog" />
      </template>
    </PageHeader>

    <nav class="netscalers-nav">
      <ul class="netscalers-nav-list">
        <li
          v-for="tab in tabs"
          :key="tab.key"
          class="netscalers-nav-item"
          :class="{ 'is-active': activeTab === tab.key }"
        >
          <a class="netscalers-nav-link" @click="selectTab(tab.key)">
            <i :class="[tab.icon, 'netscalers-nav-icon']" />
            <span>{{ tab.label }}</span>
          </a>
        </li>
      </ul>
    </nav>

    <div v-show="activeTab === 'inventory'" class="content-panel">
      <DataTable
        class="netscalers-table"
        :value="filteredAppliances"
        :loading="loading"
        striped-rows
        paginator
        :rows="10"
        :rows-per-page-options="[10, 25, 50]"
        empty-message="No NetScalers found. Add your first appliance to get started."
      >
        <Column field="name" header="Name" sortable />
        <Column field="environment" header="Environment" sortable>
          <template #body="{ data }">
            <Tag :value="data.environment" :severity="environmentSeverity(data.environment)" />
          </template>
        </Column>
        <Column header="Status">
          <template #body="{ data }">
            <Tag
              :value="data.enabled ? 'Enabled' : 'Disabled'"
              :severity="data.enabled ? 'success' : 'secondary'"
            />
          </template>
        </Column>
        <Column field="notes" header="Notes">
          <template #body="{ data }">
            <span class="notes-cell">{{ data.notes || '—' }}</span>
          </template>
        </Column>
        <Column headerClass="actions-col" bodyClass="actions-col" style="min-width: 12rem">
          <template #header>
            <span class="actions-header">Actions</span>
          </template>
          <template #body="{ data }">
            <div class="actions-cell flex gap-1">
              <Button
                v-tooltip="tooltip('Inspect via MCP')"
                icon="pi pi-search"
                text
                rounded
                size="small"
                :loading="inspectingId === data.id"
                @click="inspectAppliance(data)"
              />
              <Button
                v-tooltip="tooltip('Test connection')"
                icon="pi pi-bolt"
                text
                rounded
                size="small"
                severity="info"
                :loading="testingId === data.id"
                @click="testAppliance(data)"
              />
              <Button
                v-tooltip="tooltip('Edit NetScaler')"
                icon="pi pi-pencil"
                text
                rounded
                size="small"
                @click="openEditDialog(data)"
              />
              <Button
                v-tooltip="tooltip(data.enabled ? 'Disable' : 'Enable')"
                :icon="data.enabled ? 'pi pi-ban' : 'pi pi-check'"
                text
                rounded
                size="small"
                :severity="data.enabled ? 'secondary' : 'success'"
                @click="toggleEnabled(data)"
              />
              <Button
                v-tooltip="tooltip('Delete NetScaler')"
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

    <div v-show="activeTab === 'ssl'">
      <SslCsrPanel />
    </div>

    <Dialog
      v-model:visible="dialogVisible"
      :header="isEditing ? 'Edit NetScaler' : 'Add NetScaler'"
      modal
      :style="{ width: 'min(32rem, 92vw)' }"
      :draggable="false"
    >
      <div class="flex flex-column gap-3">
        <div class="flex flex-column gap-2">
          <label for="name" class="field-label">Name</label>
          <InputText id="name" v-model="form.name" class="w-full" />
        </div>
        <div class="flex flex-column gap-2">
          <label for="environment" class="field-label">Environment</label>
          <Select id="environment" v-model="form.environment" :options="environments" class="w-full" />
        </div>
        <div class="flex flex-column gap-2">
          <label for="host" class="field-label">Hostname / IP</label>
          <InputText id="host" v-model="form.host" class="w-full" placeholder="10.0.0.1 or ns.example.com" />
          <small class="field-hint">HTTPS on port 443 (Next-Gen API). Example: 192.168.1.10 or adc.corp.local</small>
          <small v-if="isEditing" class="field-hint">Leave blank to keep existing value.</small>
        </div>
        <div class="flex flex-column gap-2">
          <label for="username" class="field-label">Username</label>
          <InputText id="username" v-model="form.username" class="w-full" />
          <small v-if="isEditing" class="field-hint">Leave blank to keep existing value.</small>
        </div>
        <div class="flex flex-column gap-2">
          <label for="password" class="field-label">Password</label>
          <Password
            id="password"
            v-model="form.password"
            class="w-full"
            :feedback="false"
            toggle-mask
            input-class="w-full"
          />
          <small v-if="isEditing" class="field-hint">Leave blank to keep existing value.</small>
        </div>
        <div class="flex flex-column gap-2">
          <label for="notes" class="field-label">Notes</label>
          <Textarea id="notes" v-model="form.notes" rows="3" class="w-full" />
        </div>
        <div class="flex align-items-center gap-2">
          <ToggleSwitch v-model="form.enabled" input-id="enabled" />
          <label for="enabled" class="field-label mb-0">Enabled</label>
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
          @click="testApplianceFromDialog"
        />
        <Button label="Save" icon="pi pi-check" @click="saveAppliance" :loading="saving" />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="inspectVisible"
      :header="inspectTitle"
      modal
      :style="{ width: 'min(42rem, 94vw)' }"
      :draggable="false"
    >
      <TabView v-if="inspectData">
        <TabPanel header="System Info">
          <div class="inspect-grid">
            <div v-for="(value, key) in inspectData.systemInfo" :key="key" class="inspect-row">
              <span class="inspect-label">{{ formatLabel(key) }}</span>
              <span class="inspect-value">{{ value || '—' }}</span>
            </div>
          </div>
        </TabPanel>
        <TabPanel header="Applications">
          <DataTable :value="inspectData.applications" size="small" striped-rows>
            <Column field="name" header="Name" />
            <Column field="virtualIp" header="Virtual IP" />
            <Column field="protocol" header="Protocol" />
            <Column field="port" header="Port" />
            <Column field="serverCount" header="Servers" />
            <Column field="state" header="State" />
          </DataTable>
        </TabPanel>
      </TabView>
      <div v-else class="empty-hint">No inspection data available.</div>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Select from 'primevue/select'
import TabPanel from 'primevue/tabpanel'
import TabView from 'primevue/tabview'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import PageHeader from '../components/PageHeader.vue'
import SslCsrPanel from '../components/SslCsrPanel.vue'
import api from '../services/api'

const route = useRoute()
const router = useRouter()

const tabs = [
  { key: 'inventory', label: 'Inventory', icon: 'pi pi-server' },
  { key: 'ssl', label: 'SSL Certificates', icon: 'pi pi-shield' }
]
const tabKeys = new Set(tabs.map((tab) => tab.key))
const activeTab = ref('inventory')

const headerSubtitle = computed(() =>
  activeTab.value === 'ssl'
    ? 'Generate a CSR for a CA or a self-signed certificate directly on your NetScaler'
    : 'Manage your NetScaler appliance inventory'
)

function applyTabFromQuery() {
  const tab = route.query.tab
  if (typeof tab === 'string' && tabKeys.has(tab)) {
    activeTab.value = tab
  }
}

function selectTab(key) {
  activeTab.value = key
  router.replace({ query: { ...route.query, tab: key } })
}

watch(() => route.query.tab, applyTabFromQuery)

const confirm = useConfirm()
const toast = useToast()

const appliances = ref([])
const loading = ref(false)
const saving = ref(false)
const testingId = ref(null)
const testingDialog = ref(false)
const inspectingId = ref(null)
const inspectVisible = ref(false)
const inspectTitle = ref('')
const inspectData = ref(null)
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)
const searchQuery = ref('')

const environments = ['LAB', 'DEV', 'TEST', 'UAT', 'PROD']

function tooltip(value) {
  return { value, appendTo: 'body', position: 'bottom' }
}

const emptyForm = () => ({
  name: '',
  environment: 'LAB',
  host: '',
  username: '',
  password: '',
  notes: '',
  enabled: true
})

const form = reactive(emptyForm())

const filteredAppliances = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return appliances.value
  return appliances.value.filter(
    (item) =>
      item.name.toLowerCase().includes(query) ||
      item.environment.toLowerCase().includes(query) ||
      (item.notes || '').toLowerCase().includes(query)
  )
})

function environmentSeverity(environment) {
  const map = {
    LAB: 'info',
    DEV: 'info',
    TEST: 'warn',
    UAT: 'warn',
    PROD: 'danger'
  }
  return map[environment] || 'secondary'
}

async function loadAppliances() {
  loading.value = true
  try {
    const { data } = await api.get('/appliances')
    appliances.value = data
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load NetScalers', life: 3000 })
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  isEditing.value = false
  editingId.value = null
  Object.assign(form, emptyForm())
  dialogVisible.value = true
}

function openEditDialog(appliance) {
  isEditing.value = true
  editingId.value = appliance.id
  Object.assign(form, {
    name: appliance.name,
    environment: appliance.environment,
    host: '',
    username: '',
    password: '',
    notes: appliance.notes,
    enabled: appliance.enabled
  })
  dialogVisible.value = true
}

function buildPayload() {
  const payload = {
    name: form.name,
    environment: form.environment,
    notes: form.notes,
    enabled: form.enabled
  }

  if (!isEditing.value) {
    payload.host = form.host
    payload.username = form.username
    payload.password = form.password
  } else {
    if (form.host) payload.host = form.host
    if (form.username) payload.username = form.username
    if (form.password) payload.password = form.password
  }

  return payload
}

async function saveAppliance() {
  saving.value = true
  try {
    const payload = buildPayload()
    if (isEditing.value) {
      await api.put(`/appliances/${editingId.value}`, payload)
      toast.add({ severity: 'success', summary: 'Updated', detail: 'NetScaler updated', life: 3000 })
    } else {
      await api.post('/appliances', payload)
      toast.add({ severity: 'success', summary: 'Created', detail: 'NetScaler created', life: 3000 })
    }
    dialogVisible.value = false
    await loadAppliances()
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to save NetScaler', life: 3000 })
  } finally {
    saving.value = false
  }
}

function formatLabel(key) {
  return key.replace(/([A-Z])/g, ' $1').replace(/^./, (char) => char.toUpperCase())
}

async function inspectAppliance(appliance) {
  inspectingId.value = appliance.id
  inspectData.value = null
  inspectTitle.value = `Inspect — ${appliance.name}`
  try {
    const [systemRes, lbRes] = await Promise.all([
      api.post(`/appliances/${appliance.id}/system-info`),
      api.post(`/appliances/${appliance.id}/lb-vservers`)
    ])

    if (!systemRes.data.success) {
      throw new Error(systemRes.data.message || 'Failed to fetch system info')
    }
    if (!lbRes.data.success) {
      throw new Error(lbRes.data.message || 'Failed to fetch LB vServers')
    }

    inspectData.value = {
      systemInfo: systemRes.data.data,
      applications: lbRes.data.data
    }
    inspectVisible.value = true
  } catch (error) {
    const detail = error.response?.data?.detail || error.message || 'Inspection failed'
    toast.add({ severity: 'error', summary: 'Inspect failed', detail, life: 5000 })
  } finally {
    inspectingId.value = null
  }
}

async function testAppliance(appliance) {
  testingId.value = appliance.id
  try {
    const { data } = await api.post(`/appliances/${appliance.id}/test`)
    toast.add({
      severity: data.success ? 'success' : 'error',
      summary: data.success ? 'Connection OK' : 'Connection failed',
      detail: data.message,
      life: 5000
    })
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to test connection', life: 3000 })
  } finally {
    testingId.value = null
  }
}

async function testApplianceFromDialog() {
  testingDialog.value = true
  try {
    let response
    if (isEditing.value && !form.host && !form.username && !form.password) {
      response = await api.post(`/appliances/${editingId.value}/test`)
    } else {
      if (!form.host || !form.username || !form.password) {
        toast.add({
          severity: 'warn',
          summary: 'Missing credentials',
          detail: 'Enter host, username, and password to test',
          life: 3000
        })
        return
      }
      response = await api.post('/appliances/test', {
        host: form.host,
        username: form.username,
        password: form.password
      })
    }
    toast.add({
      severity: response.data.success ? 'success' : 'error',
      summary: response.data.success ? 'Connection OK' : 'Connection failed',
      detail: response.data.message,
      life: 5000
    })
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to test connection', life: 3000 })
  } finally {
    testingDialog.value = false
  }
}

async function toggleEnabled(appliance) {
  try {
    const endpoint = appliance.enabled ? 'disable' : 'enable'
    await api.patch(`/appliances/${appliance.id}/${endpoint}`)
    await loadAppliances()
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to update status', life: 3000 })
  }
}

function confirmDelete(appliance) {
  confirm.require({
    message: `Delete "${appliance.name}"? This action cannot be undone.`,
    header: 'Confirm Delete',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await api.delete(`/appliances/${appliance.id}`)
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'NetScaler deleted', life: 3000 })
        await loadAppliances()
      } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete NetScaler', life: 3000 })
      }
    }
  })
}

onMounted(() => {
  applyTabFromQuery()
  loadAppliances()
})
</script>

<style scoped>
.page {
  animation: page-in 0.35s ease;
}

.netscalers-nav {
  border-bottom: 1px solid var(--p-content-border-color);
  overflow-x: auto;
  margin-bottom: 1.25rem;
}

.netscalers-nav-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: row;
  white-space: nowrap;
}

.netscalers-nav-item {
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.netscalers-nav-item.is-active {
  border-bottom-color: var(--p-primary-color);
}

.netscalers-nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  font-weight: 500;
  color: var(--p-text-muted-color);
  transition: color 0.15s ease;
}

.netscalers-nav-item.is-active .netscalers-nav-link {
  color: var(--p-primary-color);
}

.netscalers-nav-link:hover {
  color: var(--p-text-color);
}

.netscalers-nav-icon {
  font-size: 1rem;
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

.notes-cell {
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.netscalers-table :deep(.actions-col) {
  width: 12rem;
  min-width: 12rem;
}

.netscalers-table :deep(thead .actions-col) {
  pointer-events: none;
}

.netscalers-table :deep(tbody .actions-col) {
  position: relative;
  z-index: 1;
}

.actions-cell {
  min-height: 2rem;
  align-items: center;
}

.inspect-grid {
  display: grid;
  gap: 0.75rem;
}

.inspect-row {
  display: grid;
  grid-template-columns: 9rem 1fr;
  gap: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--p-content-border-color);
}

.inspect-label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
}

.inspect-value {
  font-size: 0.875rem;
  word-break: break-word;
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
