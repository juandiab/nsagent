<template>
  <div class="page">
    <PageHeader
      title="Appliances"
      :subtitle="headerSubtitle"
      :searchable="activeTab === 'inventory'"
      v-model:search="searchQuery"
    >
      <template v-if="activeTab === 'inventory' && isAdmin" #actions>
        <Button label="Add NetScaler" icon="pi pi-server" size="small" @click="openNetScalerDialog" />
        <Button
          label="Add appliance"
          icon="pi pi-plus"
          size="small"
          severity="secondary"
          outlined
          @click="openOtherDialog"
        />
      </template>
    </PageHeader>

    <div class="content-panel vendor-support-panel">
      <h3 class="roadmap-title">Vendor support <span class="roadmap-soon">(Coming soon)</span></h3>
      <p class="roadmap-copy">
        JPilot automation is available today for NetScaler MPX and VPX. Additional platforms can be
        registered below to prepare your inventory.
      </p>
      <div class="vendor-grid">
        <div
          v-for="item in vendorSupport"
          :key="item.id"
          class="vendor-card"
          :class="{ 'vendor-card--supported': item.status === 'supported' }"
        >
          <div class="vendor-card-head">
            <span class="vendor-name">{{ item.label }}</span>
            <Tag
              :value="item.status === 'supported' ? 'Available' : 'Coming soon'"
              :severity="item.status === 'supported' ? 'success' : 'secondary'"
            />
          </div>
          <p class="vendor-desc">{{ item.description }}</p>
        </div>
      </div>
    </div>

    <nav class="appliances-nav">
      <ul class="appliances-nav-list">
        <li
          v-for="tab in tabs"
          :key="tab.key"
          class="appliances-nav-item"
          :class="{ 'is-active': activeTab === tab.key }"
        >
          <a class="appliances-nav-link" @click="selectTab(tab.key)">
            <i :class="[tab.icon, 'appliances-nav-icon']" />
            <span>{{ tab.label }}</span>
          </a>
        </li>
      </ul>
    </nav>

    <div v-show="activeTab === 'inventory'" class="content-panel">
      <DataTable
        class="appliances-table"
        :value="filteredAppliances"
        :loading="loading"
        striped-rows
        paginator
        :rows="10"
        :rows-per-page-options="[10, 25, 50]"
        empty-message="No appliances registered yet. Add a NetScaler or another vendor to get started."
      >
        <Column field="name" header="Name" sortable />
        <Column header="Platform" sortable sort-field="vendor">
          <template #body="{ data }">
            <Tag
              :value="platformLabel(data)"
              :severity="isNetScalerVendor(data.vendor) ? 'success' : 'info'"
            />
          </template>
        </Column>
        <Column field="environment" header="Environment" sortable>
          <template #body="{ data }">
            <Tag :value="data.environment" :severity="environmentSeverity(data.environment)" />
          </template>
        </Column>
        <Column header="JPilot">
          <template #body="{ data }">
            <Tag
              v-if="isNetScalerVendor(data.vendor)"
              :value="data.enabled ? 'Enabled' : 'Disabled'"
              :severity="data.enabled ? 'success' : 'secondary'"
            />
            <Tag v-else value="Coming soon" severity="secondary" icon="pi pi-clock" />
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
            <div v-if="isNetScalerVendor(data.vendor)" class="actions-cell flex gap-1">
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
                @click="testNetScaler(data)"
              />
              <Button
                v-tooltip="adminTooltip('Edit NetScaler')"
                icon="pi pi-pencil"
                text
                rounded
                size="small"
                :disabled="!isAdmin"
                @click="openNetScalerEdit(data)"
              />
              <Button
                v-tooltip="adminTooltip(data.enabled ? 'Disable' : 'Enable')"
                :icon="data.enabled ? 'pi pi-ban' : 'pi pi-check'"
                text
                rounded
                size="small"
                :severity="data.enabled ? 'secondary' : 'success'"
                :disabled="!isAdmin"
                @click="toggleEnabled(data)"
              />
              <Button
                v-tooltip="adminTooltip('Delete')"
                icon="pi pi-trash"
                text
                rounded
                size="small"
                severity="danger"
                :disabled="!isAdmin"
                @click="confirmDelete(data, 'NetScaler')"
              />
            </div>
            <div v-else class="actions-cell flex gap-1">
              <Button
                v-tooltip="tooltip('Edit appliance')"
                icon="pi pi-pencil"
                text
                rounded
                size="small"
                @click="openOtherEdit(data)"
              />
              <Button
                v-tooltip="tooltip('Delete appliance')"
                icon="pi pi-trash"
                text
                rounded
                size="small"
                severity="danger"
                @click="confirmDelete(data, 'appliance')"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <div v-show="activeTab === 'ssl'">
      <SslCsrPanel />
    </div>

    <!-- NetScaler dialog -->
    <Dialog
      v-model:visible="netScalerDialogVisible"
      :header="netScalerEditing ? 'Edit NetScaler' : 'Add NetScaler'"
      modal
      :style="{ width: 'min(32rem, 92vw)' }"
      :draggable="false"
    >
      <div class="flex flex-column gap-3">
        <div class="flex flex-column gap-2">
          <label for="ns-name" class="field-label">Name</label>
          <InputText id="ns-name" v-model="netScalerForm.name" class="w-full" />
        </div>
        <div class="flex flex-column gap-2">
          <label for="ns-environment" class="field-label">Environment</label>
          <Select id="ns-environment" v-model="netScalerForm.environment" :options="environments" class="w-full" />
        </div>
        <div class="flex flex-column gap-2">
          <label for="ns-host" class="field-label">Hostname / IP</label>
          <InputText id="ns-host" v-model="netScalerForm.host" class="w-full" placeholder="10.0.0.1 or ns.example.com" />
          <small class="field-hint">HTTPS on port 443 (Next-Gen API).</small>
          <small v-if="netScalerEditing" class="field-hint">Leave blank to keep existing value.</small>
        </div>
        <div class="flex flex-column gap-2">
          <label for="ns-username" class="field-label">Username</label>
          <InputText id="ns-username" v-model="netScalerForm.username" class="w-full" />
          <small v-if="netScalerEditing" class="field-hint">Leave blank to keep existing value.</small>
        </div>
        <div class="flex flex-column gap-2">
          <label for="ns-password" class="field-label">Password</label>
          <Password
            id="ns-password"
            v-model="netScalerForm.password"
            class="w-full"
            :feedback="false"
            toggle-mask
            input-class="w-full"
          />
          <small v-if="netScalerEditing" class="field-hint">Leave blank to keep existing value.</small>
        </div>
        <div class="flex flex-column gap-2">
          <label for="ns-notes" class="field-label">Notes</label>
          <Textarea id="ns-notes" v-model="netScalerForm.notes" rows="3" class="w-full" />
        </div>
        <div class="flex align-items-center gap-2">
          <ToggleSwitch v-model="netScalerForm.enabled" input-id="ns-enabled" />
          <label for="ns-enabled" class="field-label mb-0">Enabled in JPilot</label>
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" text severity="secondary" @click="netScalerDialogVisible = false" />
        <Button
          label="Test"
          icon="pi pi-bolt"
          severity="info"
          outlined
          :loading="testingDialog"
          @click="testNetScalerFromDialog"
        />
        <Button label="Save" icon="pi pi-check" @click="saveNetScaler" :loading="saving" />
      </template>
    </Dialog>

    <!-- Other vendor dialog -->
    <Dialog
      v-model:visible="otherDialogVisible"
      :header="otherEditing ? 'Edit appliance' : 'Add appliance'"
      modal
      :style="{ width: 'min(32rem, 92vw)' }"
      :draggable="false"
    >
      <Message severity="warn" :closable="false" class="mb-3">
        Credentials are stored for future automation. JPilot chat is not enabled for this vendor yet.
      </Message>
      <div class="flex flex-column gap-3">
        <div class="flex flex-column gap-2">
          <label for="vendor" class="field-label">Vendor</label>
          <Select
            id="vendor"
            v-model="otherForm.vendor"
            :options="vendorOptions"
            option-label="label"
            option-value="value"
            class="w-full"
            :disabled="otherEditing"
          />
          <small v-if="selectedVendor" class="field-hint">{{ selectedVendor.description }}</small>
        </div>
        <div class="flex flex-column gap-2">
          <label for="name" class="field-label">Name</label>
          <InputText id="name" v-model="otherForm.name" class="w-full" />
        </div>
        <div class="flex flex-column gap-2">
          <label for="environment" class="field-label">Environment</label>
          <Select id="environment" v-model="otherForm.environment" :options="environments" class="w-full" />
        </div>
        <div class="flex flex-column gap-2">
          <label for="host" class="field-label">Hostname / IP</label>
          <InputText id="host" v-model="otherForm.host" class="w-full" placeholder="10.0.0.1 or device.example.com" />
          <small class="field-hint">Management IP or hostname for SSH and/or HTTPS API access.</small>
          <small v-if="otherEditing" class="field-hint">Leave blank to keep existing value.</small>
        </div>
        <div class="flex flex-column gap-2">
          <label for="username" class="field-label">Username</label>
          <InputText id="username" v-model="otherForm.username" class="w-full" />
          <small v-if="otherEditing" class="field-hint">Leave blank to keep existing value.</small>
        </div>
        <div class="flex flex-column gap-2">
          <label for="password" class="field-label">Password</label>
          <Password
            id="password"
            v-model="otherForm.password"
            class="w-full"
            :feedback="false"
            toggle-mask
            input-class="w-full"
          />
          <small v-if="otherEditing" class="field-hint">Leave blank to keep existing value.</small>
        </div>
        <div class="flex flex-column gap-2">
          <label for="notes" class="field-label">Notes</label>
          <Textarea id="notes" v-model="otherForm.notes" rows="3" class="w-full" />
        </div>
      </div>
      <template #footer>
        <Button label="Cancel" text severity="secondary" @click="otherDialogVisible = false" />
        <Button label="Save" icon="pi pi-check" @click="saveOtherAppliance" :loading="saving" />
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
import Message from 'primevue/message'
import Password from 'primevue/password'
import Select from 'primevue/select'
import TabPanel from 'primevue/tabpanel'
import TabView from 'primevue/tabview'
import Tag from 'primevue/tag'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import PageHeader from '../components/PageHeader.vue'
import SslCsrPanel from '../components/SslCsrPanel.vue'
import {
  isNetScalerVendor,
  NETSCALER_VENDOR,
  OTHER_APPLIANCE_VENDORS,
  VENDOR_SUPPORT,
  vendorLabel
} from '../config/applianceVendors'
import api from '../services/api'
import { getStoredUser } from '../services/auth'

const route = useRoute()
const router = useRouter()
const confirm = useConfirm()
const toast = useToast()

const vendorSupport = VENDOR_SUPPORT
const vendorOptions = OTHER_APPLIANCE_VENDORS

const currentUser = ref(getStoredUser())
const isAdmin = computed(() => currentUser.value?.role === 'admin')

const tabs = [
  { key: 'inventory', label: 'Inventory', icon: 'pi pi-server' },
  { key: 'ssl', label: 'SSL Certificates', icon: 'pi pi-shield' }
]
const tabKeys = new Set(tabs.map((tab) => tab.key))
const activeTab = ref('inventory')

const headerSubtitle = computed(() => {
  if (activeTab.value === 'ssl') {
    return 'Generate a CSR or self-signed certificate on your NetScaler'
  }
  return 'NetScaler MPX/VPX inventory and multi-vendor registry'
})

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

const appliances = ref([])
const loading = ref(false)
const saving = ref(false)
const testingId = ref(null)
const testingDialog = ref(false)
const inspectingId = ref(null)
const inspectVisible = ref(false)
const inspectTitle = ref('')
const inspectData = ref(null)
const searchQuery = ref('')

const netScalerDialogVisible = ref(false)
const netScalerEditing = ref(false)
const netScalerEditingId = ref(null)

const otherDialogVisible = ref(false)
const otherEditing = ref(false)
const otherEditingId = ref(null)

const environments = ['LAB', 'DEV', 'TEST', 'UAT', 'PROD']

function tooltip(value) {
  return { value, appendTo: 'body', position: 'bottom' }
}

function adminTooltip(value) {
  if (!isAdmin.value) {
    return { value: `${value} (admin only)`, appendTo: 'body', position: 'bottom' }
  }
  return tooltip(value)
}

function platformLabel(appliance) {
  return isNetScalerVendor(appliance.vendor) ? 'NetScaler MPX/VPX' : vendorLabel(appliance.vendor)
}

const emptyNetScalerForm = () => ({
  name: '',
  environment: 'LAB',
  host: '',
  username: '',
  password: '',
  notes: '',
  enabled: true
})

const netScalerForm = reactive(emptyNetScalerForm())

const emptyOtherForm = () => ({
  vendor: 'f5',
  name: '',
  environment: 'LAB',
  host: '',
  username: '',
  password: '',
  notes: ''
})

const otherForm = reactive(emptyOtherForm())

const selectedVendor = computed(() => vendorOptions.find((item) => item.value === otherForm.vendor))

const filteredAppliances = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  const items = appliances.value
  if (!query) return items
  return items.filter(
    (item) =>
      item.name.toLowerCase().includes(query) ||
      item.environment.toLowerCase().includes(query) ||
      platformLabel(item).toLowerCase().includes(query) ||
      vendorLabel(item.vendor).toLowerCase().includes(query) ||
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
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load appliances', life: 3000 })
  } finally {
    loading.value = false
  }
}

function openNetScalerDialog() {
  netScalerEditing.value = false
  netScalerEditingId.value = null
  Object.assign(netScalerForm, emptyNetScalerForm())
  netScalerDialogVisible.value = true
}

function openNetScalerEdit(appliance) {
  netScalerEditing.value = true
  netScalerEditingId.value = appliance.id
  Object.assign(netScalerForm, {
    name: appliance.name,
    environment: appliance.environment,
    host: '',
    username: '',
    password: '',
    notes: appliance.notes,
    enabled: appliance.enabled
  })
  netScalerDialogVisible.value = true
}

function openOtherDialog() {
  otherEditing.value = false
  otherEditingId.value = null
  Object.assign(otherForm, emptyOtherForm())
  otherDialogVisible.value = true
}

function openOtherEdit(appliance) {
  otherEditing.value = true
  otherEditingId.value = appliance.id
  Object.assign(otherForm, {
    vendor: appliance.vendor,
    name: appliance.name,
    environment: appliance.environment,
    host: '',
    username: '',
    password: '',
    notes: appliance.notes
  })
  otherDialogVisible.value = true
}

function buildNetScalerPayload() {
  const payload = {
    vendor: NETSCALER_VENDOR,
    name: netScalerForm.name,
    environment: netScalerForm.environment,
    notes: netScalerForm.notes,
    enabled: netScalerForm.enabled
  }
  if (!netScalerEditing.value) {
    payload.host = netScalerForm.host
    payload.username = netScalerForm.username
    payload.password = netScalerForm.password
  } else {
    if (netScalerForm.host) payload.host = netScalerForm.host
    if (netScalerForm.username) payload.username = netScalerForm.username
    if (netScalerForm.password) payload.password = netScalerForm.password
  }
  return payload
}

function buildOtherPayload() {
  const payload = {
    vendor: otherForm.vendor,
    name: otherForm.name,
    environment: otherForm.environment,
    notes: otherForm.notes,
    enabled: false
  }
  if (!otherEditing.value) {
    payload.host = otherForm.host
    payload.username = otherForm.username
    payload.password = otherForm.password
  } else {
    if (otherForm.host) payload.host = otherForm.host
    if (otherForm.username) payload.username = otherForm.username
    if (otherForm.password) payload.password = otherForm.password
  }
  return payload
}

async function saveNetScaler() {
  saving.value = true
  try {
    const payload = buildNetScalerPayload()
    if (netScalerEditing.value) {
      await api.put(`/appliances/${netScalerEditingId.value}`, payload)
      toast.add({ severity: 'success', summary: 'Updated', detail: 'NetScaler updated', life: 3000 })
    } else {
      await api.post('/appliances', payload)
      toast.add({ severity: 'success', summary: 'Created', detail: 'NetScaler created', life: 3000 })
    }
    netScalerDialogVisible.value = false
    await loadAppliances()
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to save NetScaler', life: 3000 })
  } finally {
    saving.value = false
  }
}

async function saveOtherAppliance() {
  if (!otherForm.vendor || isNetScalerVendor(otherForm.vendor)) {
    toast.add({
      severity: 'warn',
      summary: 'Vendor required',
      detail: 'Use Add NetScaler for MPX/VPX appliances.',
      life: 4000
    })
    return
  }
  saving.value = true
  try {
    const payload = buildOtherPayload()
    if (otherEditing.value) {
      await api.put(`/appliances/${otherEditingId.value}`, payload)
      toast.add({ severity: 'success', summary: 'Updated', detail: 'Appliance saved', life: 3000 })
    } else {
      await api.post('/appliances', payload)
      toast.add({
        severity: 'success',
        summary: 'Created',
        detail: 'Appliance registered — JPilot support coming soon',
        life: 4000
      })
    }
    otherDialogVisible.value = false
    await loadAppliances()
  } catch {
    toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to save appliance', life: 3000 })
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

async function testNetScaler(appliance) {
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

async function testNetScalerFromDialog() {
  testingDialog.value = true
  try {
    let response
    if (netScalerEditing.value && !netScalerForm.host && !netScalerForm.username && !netScalerForm.password) {
      response = await api.post(`/appliances/${netScalerEditingId.value}/test`)
    } else {
      if (!netScalerForm.host || !netScalerForm.username || !netScalerForm.password) {
        toast.add({
          severity: 'warn',
          summary: 'Missing credentials',
          detail: 'Enter host, username, and password to test',
          life: 3000
        })
        return
      }
      response = await api.post('/appliances/test', {
        host: netScalerForm.host,
        username: netScalerForm.username,
        password: netScalerForm.password
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

function confirmDelete(appliance, label) {
  confirm.require({
    message: `Delete "${appliance.name}"? This action cannot be undone.`,
    header: 'Confirm Delete',
    icon: 'pi pi-exclamation-triangle',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await api.delete(`/appliances/${appliance.id}`)
        toast.add({ severity: 'success', summary: 'Deleted', detail: `${label} removed`, life: 3000 })
        await loadAppliances()
      } catch {
        toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to delete', life: 3000 })
      }
    }
  })
}

onMounted(() => {
  applyTabFromQuery()
  loadAppliances()
  api
    .get('/auth/me')
    .then(({ data }) => {
      currentUser.value = data
    })
    .catch(() => {})
})
</script>

<style scoped>
.page {
  animation: page-in 0.35s ease;
}

.vendor-support-panel {
  margin-bottom: 1.25rem;
  padding: 1.25rem;
}

.roadmap-title {
  margin: 0 0 0.35rem;
  font-size: 1rem;
  font-weight: 600;
}

.roadmap-soon {
  font-weight: 500;
  color: var(--p-text-muted-color);
}

.roadmap-copy {
  margin: 0 0 1rem;
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.vendor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(16rem, 1fr));
  gap: 0.75rem;
}

.vendor-card {
  border: 1px solid var(--p-content-border-color);
  border-radius: 0.75rem;
  padding: 0.875rem;
  background: var(--app-nested-surface);
}

.vendor-card--supported {
  border-color: color-mix(in srgb, var(--p-green-500) 55%, var(--p-content-border-color));
  background: color-mix(in srgb, var(--p-green-50) 35%, var(--app-nested-surface));
}

.vendor-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}

.vendor-name {
  font-weight: 600;
  font-size: 0.875rem;
}

.vendor-desc {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
}

.appliances-nav {
  border-bottom: 1px solid var(--p-content-border-color);
  overflow-x: auto;
  margin-bottom: 1.25rem;
}

.appliances-nav-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: row;
  white-space: nowrap;
}

.appliances-nav-item {
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.appliances-nav-item.is-active {
  border-bottom-color: var(--p-primary-color);
}

.appliances-nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  font-weight: 500;
  color: var(--p-text-muted-color);
  transition: color 0.15s ease;
}

.appliances-nav-item.is-active .appliances-nav-link {
  color: var(--p-primary-color);
}

.appliances-nav-link:hover {
  color: var(--p-text-color);
}

.appliances-nav-icon {
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

.appliances-table :deep(.actions-col) {
  width: 12rem;
  min-width: 12rem;
}

.appliances-table :deep(thead .actions-col) {
  pointer-events: none;
}

.appliances-table :deep(tbody .actions-col) {
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
