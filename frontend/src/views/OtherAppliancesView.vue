<template>
  <div class="page">
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

    <div
      v-if="activeTab === 'inventory'"
      class="appliances-toolbar flex flex-column sm:flex-row sm:align-items-center sm:justify-content-between gap-2 mb-3"
    >
      <span class="appliances-search p-input-icon-left">
        <i class="pi pi-search" />
        <InputText v-model="searchQuery" placeholder="Search" size="small" class="search-input" />
      </span>
      <Button
        v-if="isAdmin"
        label="Add appliance"
        icon="pi pi-plus"
        size="small"
        @click="openAddDialog"
      />
    </div>

    <div v-if="activeTab === 'inventory' && inventoryTags.length" class="tag-filters flex flex-wrap align-items-center gap-2 mb-3">
      <span class="tag-filters-label">Tags</span>
      <Button
        v-for="tag in inventoryTags"
        :key="tag"
        :label="tag"
        size="small"
        rounded
        :outlined="activeTagFilter !== tag"
        :severity="activeTagFilter === tag ? 'info' : 'secondary'"
        @click="toggleTagFilter(tag)"
      />
      <Button
        v-if="activeTagFilter"
        label="Clear"
        size="small"
        text
        severity="secondary"
        @click="activeTagFilter = ''"
      />
    </div>

    <div v-show="activeTab === 'inventory'" class="content-panel">
      <DataTable
        class="appliances-table"
        :value="filteredAppliances"
        :loading="loading"
        striped-rows
        paginator
        :rows="10"
        :rows-per-page-options="[10, 25, 50]"
        empty-message="No appliances registered yet. Use Add appliance to get started."
      >
        <Column field="name" header="Name" sortable />
        <Column header="Platform" sortable sort-field="vendor">
          <template #body="{ data }">
            <Tag :value="platformLabel(data)" :severity="data.copilotEligible ? 'success' : 'info'" />
          </template>
        </Column>
        <Column field="environment" header="Environment" sortable>
          <template #body="{ data }">
            <Tag :value="data.environment" :severity="environmentSeverity(data.environment)" />
          </template>
        </Column>
        <Column header="Tags">
          <template #body="{ data }">
            <div v-if="data.tags?.length" class="tag-cell flex flex-wrap gap-1">
              <Tag
                v-for="tag in data.tags"
                :key="`${data.id}-${tag}`"
                :value="tag"
                severity="secondary"
                class="tag-chip"
                @click="toggleTagFilter(tag)"
              />
            </div>
            <span v-else class="notes-cell">—</span>
          </template>
        </Column>
        <Column header="JPilot">
          <template #body="{ data }">
            <Tag
              v-if="data.copilotEligible"
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
            <div class="actions-cell flex gap-1">
              <Button
                v-if="supportsInspect(data)"
                v-tooltip="tooltip('Inspect via MCP')"
                icon="pi pi-search"
                text
                rounded
                size="small"
                :loading="inspectingId === data.id"
                @click="inspectAppliance(data)"
              />
              <Button
                v-if="supportsConnectionTest(data)"
                v-tooltip="tooltip('Test connection')"
                icon="pi pi-bolt"
                text
                rounded
                size="small"
                severity="info"
                :loading="testingId === data.id"
                @click="testConnection(data)"
              />
              <Button
                v-tooltip="adminTooltip('Edit appliance')"
                icon="pi pi-pencil"
                text
                rounded
                size="small"
                :disabled="!isAdmin"
                @click="openEditDialog(data)"
              />
              <Button
                v-if="data.copilotEligible"
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
                @click="confirmDelete(data)"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>

    <div v-show="activeTab === 'inventory'" class="content-panel vendor-support-panel">
      <h3 class="roadmap-title">Vendor support</h3>
      <p class="roadmap-copy">
        JPilot automation availability by platform. Register any product to prepare your inventory;
        supported platforms can be enabled for chat.
      </p>
      <div class="vendor-grid">
        <div
          v-for="item in vendorSupport"
          :key="item.id"
          class="vendor-card"
          :class="{ 'vendor-card--supported': item.status === 'supported' }"
        >
          <div class="vendor-card-head">
            <div class="vendor-card-titles">
              <span class="vendor-name">{{ item.label }}</span>
              <span class="vendor-family">{{ item.vendorGroupLabel }}</span>
            </div>
            <Tag
              :value="item.status === 'supported' ? 'Available' : 'Coming soon'"
              :severity="item.status === 'supported' ? 'success' : 'secondary'"
            />
          </div>
          <p class="vendor-desc">{{ item.description }}</p>
        </div>
      </div>
    </div>

    <div v-show="activeTab === 'ssl'">
      <SslCsrPanel />
    </div>

    <Dialog
      v-model:visible="dialogVisible"
      :header="editing ? 'Edit appliance' : 'Add appliance'"
      modal
      :style="{ width: 'min(34rem, 92vw)' }"
      :draggable="false"
      @hide="resetAddWizard"
    >
      <!-- Add: stepped flow — vendor → device → details -->
      <div v-if="!editing" class="flex flex-column gap-3">
        <div v-if="addStep > 1" class="wizard-trail">
          <button type="button" class="wizard-trail-link" @click="goToAddStep(1)">
            {{ selectedVendorGroup?.label }}
          </button>
          <span v-if="addStep >= 2" class="wizard-trail-sep">/</span>
          <button
            v-if="addStep >= 2 && selectedProduct"
            type="button"
            class="wizard-trail-link"
            :disabled="addStep === 2"
            @click="goToAddStep(2)"
          >
            {{ selectedProduct.label }}
          </button>
        </div>

        <div v-if="addStep === 1" class="wizard-step">
          <p class="step-title">Select vendor</p>
          <div class="picker-list">
            <button
              v-for="group in vendorGroups"
              :key="group.id"
              type="button"
              class="picker-item"
              @click="selectVendor(group.id)"
            >
              <span class="picker-item-label">{{ group.label }}</span>
              <i class="pi pi-chevron-right picker-item-chevron" />
            </button>
          </div>
        </div>

        <div v-else-if="addStep === 2" class="wizard-step">
          <p class="step-title">Select device</p>
          <div class="picker-list">
            <button
              v-for="option in productOptions"
              :key="option.id"
              type="button"
              class="picker-item"
              :class="{ 'picker-item--soon': option.disabled }"
              @click="selectProduct(option.id)"
            >
              <span class="picker-item-label">{{ option.label }}</span>
              <span
                class="picker-item-status"
                :class="option.disabled ? 'picker-item-status--soon' : 'picker-item-status--ok'"
              >
                {{ option.statusLabel }}
              </span>
            </button>
          </div>
        </div>

        <div v-else-if="addStep === 3" class="wizard-step">
          <p class="step-title">{{ selectedProduct?.label }}</p>
          <small v-if="selectedProduct?.description" class="field-hint block mb-2">
            {{ selectedProduct.description }}
          </small>

          <div v-if="!productIsSupported" class="unsupported-panel">
            <i class="pi pi-clock unsupported-icon" />
            <p class="unsupported-title">Device not supported yet, coming soon</p>
            <p class="unsupported-copy">
              JPilot automation for {{ selectedProduct?.label }} is not available yet. Pick another device
              or check Vendor support below the inventory for the roadmap.
            </p>
          </div>

          <template v-else>
            <div class="flex flex-column gap-2">
              <label for="appliance-name" class="field-label">Name</label>
              <InputText id="appliance-name" v-model="form.name" class="w-full" />
            </div>
            <div class="flex flex-column gap-2">
              <label for="appliance-environment" class="field-label">Environment</label>
              <Select
                id="appliance-environment"
                v-model="form.environment"
                :options="environments"
                class="w-full"
              />
            </div>
            <div class="flex flex-column gap-2">
              <label for="appliance-host" class="field-label">Hostname / IP</label>
              <InputText
                id="appliance-host"
                v-model="form.host"
                class="w-full"
                placeholder="10.0.0.1 or device.example.com"
              />
              <small class="field-hint">{{ selectedProduct?.hostHint || 'Management IP or hostname.' }}</small>
            </div>
            <div class="flex flex-column gap-2">
              <label for="appliance-username" class="field-label">Username</label>
              <InputText id="appliance-username" v-model="form.username" class="w-full" />
            </div>
            <div class="flex flex-column gap-2">
              <label for="appliance-password" class="field-label">Password</label>
              <Password
                id="appliance-password"
                v-model="form.password"
                class="w-full"
                :feedback="false"
                toggle-mask
                input-class="w-full"
              />
            </div>
            <div class="flex flex-column gap-2">
              <label for="appliance-notes" class="field-label">Notes</label>
              <Textarea id="appliance-notes" v-model="form.notes" rows="3" class="w-full" />
            </div>
            <div class="flex flex-column gap-2">
              <label for="appliance-tags" class="field-label">Tags</label>
              <Chips
                id="appliance-tags"
                v-model="form.tags"
                separator=","
                placeholder="Type a tag and press Enter"
                class="w-full"
              />
              <small class="field-hint">Use tags like prod, dmz, or team-east to filter inventory later.</small>
            </div>
            <div
              v-if="selectedProduct?.value && isCopilotEligibleVendor(selectedProduct.value)"
              class="flex align-items-center gap-2"
            >
              <ToggleSwitch v-model="form.enabled" input-id="appliance-enabled" />
              <label for="appliance-enabled" class="field-label mb-0">Enabled in JPilot</label>
            </div>
          </template>
        </div>
      </div>

      <!-- Edit: single form -->
      <div v-else class="flex flex-column gap-3">
        <div class="flex flex-column gap-2">
          <label class="field-label">Vendor</label>
          <InputText :model-value="selectedVendorGroup?.label || '—'" class="w-full" disabled />
        </div>
        <div class="flex flex-column gap-2">
          <label class="field-label">Device / platform</label>
          <InputText :model-value="selectedProduct?.label || '—'" class="w-full" disabled />
        </div>
        <template v-if="showApplianceFields">
          <div class="flex flex-column gap-2">
            <label for="edit-appliance-name" class="field-label">Name</label>
            <InputText id="edit-appliance-name" v-model="form.name" class="w-full" />
          </div>
          <div class="flex flex-column gap-2">
            <label for="edit-appliance-environment" class="field-label">Environment</label>
            <Select
              id="edit-appliance-environment"
              v-model="form.environment"
              :options="environments"
              class="w-full"
            />
          </div>
          <div class="flex flex-column gap-2">
            <label for="edit-appliance-host" class="field-label">Hostname / IP</label>
            <InputText id="edit-appliance-host" v-model="form.host" class="w-full" />
            <small class="field-hint">Leave blank to keep existing value.</small>
          </div>
          <div class="flex flex-column gap-2">
            <label for="edit-appliance-username" class="field-label">Username</label>
            <InputText id="edit-appliance-username" v-model="form.username" class="w-full" />
            <small class="field-hint">Leave blank to keep existing value.</small>
          </div>
          <div class="flex flex-column gap-2">
            <label for="edit-appliance-password" class="field-label">Password</label>
            <Password
              id="edit-appliance-password"
              v-model="form.password"
              class="w-full"
              :feedback="false"
              toggle-mask
              input-class="w-full"
            />
            <small class="field-hint">Leave blank to keep existing value.</small>
          </div>
          <div class="flex flex-column gap-2">
            <label for="edit-appliance-notes" class="field-label">Notes</label>
            <Textarea id="edit-appliance-notes" v-model="form.notes" rows="3" class="w-full" />
          </div>
          <div class="flex flex-column gap-2">
            <label for="edit-appliance-tags" class="field-label">Tags</label>
            <Chips
              id="edit-appliance-tags"
              v-model="form.tags"
              separator=","
              placeholder="Type a tag and press Enter"
              class="w-full"
            />
          </div>
          <div
            v-if="selectedProduct?.value && isCopilotEligibleVendor(selectedProduct.value)"
            class="flex align-items-center gap-2"
          >
            <ToggleSwitch v-model="form.enabled" input-id="edit-appliance-enabled" />
            <label for="edit-appliance-enabled" class="field-label mb-0">Enabled in JPilot</label>
          </div>
        </template>
      </div>

      <template #footer>
        <Button label="Cancel" text severity="secondary" @click="dialogVisible = false" />
        <Button v-if="!editing && addStep > 1" label="Back" text severity="secondary" @click="goBackAddStep" />
        <Button
          v-if="editing && showApplianceFields && supportsConnectionTestForForm"
          label="Test"
          icon="pi pi-bolt"
          severity="info"
          outlined
          :loading="testingDialog"
          @click="testFromDialog"
        />
        <Button
          v-if="!editing && addStep === 3 && productIsSupported && supportsConnectionTestForForm"
          label="Test"
          icon="pi pi-bolt"
          severity="info"
          outlined
          :loading="testingDialog"
          @click="testFromDialog"
        />
        <Button
          v-if="editing || (addStep === 3 && productIsSupported)"
          label="Save"
          icon="pi pi-check"
          :disabled="!canSave"
          :loading="saving"
          @click="saveAppliance"
        />
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
import Chips from 'primevue/chips'
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
import SslCsrPanel from '../components/SslCsrPanel.vue'
import {
  getProductById,
  isCopilotEligibleVendor,
  isProductSupported,
  productSelectOptions,
  resolveApplianceProduct,
  VENDOR_GROUPS,
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
const vendorGroups = VENDOR_GROUPS

const currentUser = ref(getStoredUser())
const isAdmin = computed(() => currentUser.value?.role === 'admin')

const tabs = [
  { key: 'inventory', label: 'Inventory', icon: 'pi pi-server' },
  { key: 'ssl', label: 'SSL Certificates', icon: 'pi pi-shield' }
]
const tabKeys = new Set(tabs.map((tab) => tab.key))
const activeTab = ref('inventory')

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
const activeTagFilter = ref('')

const dialogVisible = ref(false)
const editing = ref(false)
const editingId = ref(null)
const addStep = ref(1)

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
  return vendorLabel(appliance.vendor, appliance.productId)
}

function resolveProductForAppliance(appliance) {
  return resolveApplianceProduct(appliance)
}

function supportsInspect(appliance) {
  return Boolean(resolveProductForAppliance(appliance)?.supportsInspect)
}

function supportsConnectionTest(appliance) {
  return Boolean(resolveProductForAppliance(appliance)?.supportsConnectionTest)
}

const emptyForm = () => ({
  vendorGroupId: '',
  productId: '',
  name: '',
  environment: 'LAB',
  host: '',
  username: '',
  password: '',
  notes: '',
  tags: [],
  enabled: true
})

const form = reactive(emptyForm())

const productOptions = computed(() => productSelectOptions(form.vendorGroupId))

const selectedVendorGroup = computed(() => vendorGroups.find((g) => g.id === form.vendorGroupId) || null)

const selectedProduct = computed(() => getProductById(form.productId))

const productIsSupported = computed(() => isProductSupported(selectedProduct.value))

const showApplianceFields = computed(() => {
  if (!selectedProduct.value?.value) return false
  if (editing.value) return true
  return productIsSupported.value
})

const supportsConnectionTestForForm = computed(() => Boolean(selectedProduct.value?.supportsConnectionTest))

const canSave = computed(() => {
  if (!selectedProduct.value?.value) return false
  if (!form.name.trim()) return false
  if (editing.value) return true
  if (!productIsSupported.value) return false
  return Boolean(form.host.trim() && form.username.trim() && form.password)
})

function resetAddWizard() {
  addStep.value = 1
}

function selectVendor(groupId) {
  form.vendorGroupId = groupId
  form.productId = ''
  addStep.value = 2
}

function selectProduct(productId) {
  form.productId = productId
  addStep.value = 3
}

function goBackAddStep() {
  if (addStep.value === 3) {
    addStep.value = 2
    return
  }
  if (addStep.value === 2) {
    form.vendorGroupId = ''
    form.productId = ''
    addStep.value = 1
  }
}

function goToAddStep(step) {
  if (step === 1) {
    form.vendorGroupId = ''
    form.productId = ''
    addStep.value = 1
    return
  }
  if (step === 2 && form.vendorGroupId) {
    form.productId = ''
    addStep.value = 2
  }
}

const filteredAppliances = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  const tagFilter = activeTagFilter.value.trim().toLowerCase()
  let items = appliances.value

  if (tagFilter) {
    items = items.filter((item) => (item.tags || []).includes(tagFilter))
  }

  if (!query) return items
  return items.filter(
    (item) =>
      item.name.toLowerCase().includes(query) ||
      item.environment.toLowerCase().includes(query) ||
      platformLabel(item).toLowerCase().includes(query) ||
      (item.notes || '').toLowerCase().includes(query) ||
      (item.tags || []).some((tag) => tag.includes(query))
  )
})

const inventoryTags = computed(() => {
  const tags = new Set()
  for (const item of appliances.value) {
    for (const tag of item.tags || []) {
      tags.add(tag)
    }
  }
  return [...tags].sort()
})

function normalizeTagsForApi(tags) {
  const seen = new Set()
  const result = []
  for (const raw of tags || []) {
    const tag = String(raw).trim().toLowerCase()
    if (!tag || seen.has(tag)) continue
    seen.add(tag)
    result.push(tag)
  }
  return result.slice(0, 20)
}

function toggleTagFilter(tag) {
  const normalized = String(tag).trim().toLowerCase()
  activeTagFilter.value = activeTagFilter.value === normalized ? '' : normalized
}

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

function openAddDialog() {
  editing.value = false
  editingId.value = null
  addStep.value = 1
  Object.assign(form, emptyForm())
  dialogVisible.value = true
}

function openEditDialog(appliance) {
  const product = resolveApplianceProduct(appliance)
  editing.value = true
  editingId.value = appliance.id
  Object.assign(form, {
    vendorGroupId: product?.vendorGroupId || 'other',
    productId: appliance.productId || product?.id || '',
    name: appliance.name,
    environment: appliance.environment,
    host: '',
    username: '',
    password: '',
    notes: appliance.notes,
    tags: [...(appliance.tags || [])],
    enabled: appliance.enabled
  })
  dialogVisible.value = true
}

function buildPayload() {
  const product = selectedProduct.value
  const payload = {
    vendor: product.value,
    productId: form.productId || undefined,
    name: form.name.trim(),
    environment: form.environment,
    notes: form.notes,
    tags: normalizeTagsForApi(form.tags),
    enabled: isCopilotEligibleVendor(product.value) ? form.enabled : false
  }
  if (!editing.value) {
    payload.host = form.host.trim()
    payload.username = form.username.trim()
    payload.password = form.password
  } else {
    if (form.host.trim()) payload.host = form.host.trim()
    if (form.username.trim()) payload.username = form.username.trim()
    if (form.password) payload.password = form.password
  }
  return payload
}

async function saveAppliance() {
  if (!canSave.value) return
  saving.value = true
  try {
    const payload = buildPayload()
    if (editing.value) {
      await api.put(`/appliances/${editingId.value}`, payload)
      toast.add({ severity: 'success', summary: 'Updated', detail: 'Appliance updated', life: 3000 })
    } else {
      await api.post('/appliances', payload)
      toast.add({ severity: 'success', summary: 'Created', detail: 'Appliance created', life: 3000 })
    }
    dialogVisible.value = false
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

async function testConnection(appliance) {
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

async function testFromDialog() {
  testingDialog.value = true
  try {
    let response
    if (editing.value && !form.host && !form.username && !form.password) {
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
        toast.add({ severity: 'success', summary: 'Deleted', detail: 'Appliance removed', life: 3000 })
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

.appliances-search {
  display: inline-flex;
  align-items: center;
  position: relative;
}

.appliances-search .pi-search {
  position: absolute;
  left: 0.65rem;
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
  pointer-events: none;
}

.appliances-toolbar .search-input {
  width: 100%;
  min-width: 12rem;
  padding-left: 2rem;
}

@media (min-width: 576px) {
  .appliances-toolbar .search-input {
    width: 14rem;
  }
}

.vendor-support-panel {
  margin-top: 1.25rem;
  padding: 1.25rem;
}

.roadmap-title {
  margin: 0 0 0.35rem;
  font-size: 1rem;
  font-weight: 600;
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
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}

.vendor-card-titles {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.vendor-name {
  font-weight: 600;
  font-size: 0.875rem;
}

.vendor-family {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
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

.product-select :deep(.p-select-option.p-disabled) {
  opacity: 1;
}

.wizard-trail {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
}

.wizard-trail-link {
  background: none;
  border: none;
  padding: 0;
  color: var(--p-primary-color);
  cursor: pointer;
  font: inherit;
}

.wizard-trail-link:disabled {
  color: var(--p-text-color);
  cursor: default;
}

.wizard-trail-sep {
  opacity: 0.6;
}

.step-title {
  margin: 0 0 0.75rem;
  font-size: 0.9375rem;
  font-weight: 600;
}

.picker-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.picker-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem 0.875rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: 0.625rem;
  background: var(--app-nested-surface);
  color: var(--p-text-color);
  cursor: pointer;
  text-align: left;
  transition:
    border-color 0.15s ease,
    background 0.15s ease;
}

.picker-item:hover {
  border-color: var(--p-primary-color);
  background: color-mix(in srgb, var(--p-primary-color) 6%, var(--app-nested-surface));
}

.picker-item--soon {
  opacity: 0.92;
}

.picker-item-label {
  font-weight: 500;
  font-size: 0.875rem;
}

.picker-item-chevron {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

.picker-item-status {
  flex-shrink: 0;
  font-size: 0.75rem;
  font-weight: 500;
}

.picker-item-status--ok {
  color: var(--p-green-600);
}

.picker-item-status--soon {
  color: var(--p-text-muted-color);
}

.unsupported-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.5rem;
  padding: 1.5rem 1rem;
  border: 1px dashed var(--p-content-border-color);
  border-radius: 0.75rem;
  background: var(--app-nested-surface);
}

.unsupported-icon {
  font-size: 1.75rem;
  color: var(--p-text-muted-color);
}

.unsupported-title {
  margin: 0;
  font-weight: 600;
  font-size: 0.9375rem;
}

.unsupported-copy {
  margin: 0;
  max-width: 22rem;
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
}

.block {
  display: block;
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

.text-muted {
  color: var(--p-text-muted-color);
}

.tag-filters-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--p-text-muted-color);
}

.tag-cell :deep(.tag-chip) {
  cursor: pointer;
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
