<template>
  <div class="cmd-menu">
    <button
      type="button"
      class="cmd-menu-trigger"
      :disabled="disabled"
      @click="openMenu"
    >
      <i class="pi pi-search" />
      <span>Browse recommended actions…</span>
      <span class="cmd-kbd">⌘K</span>
    </button>

    <div class="cmd-inline">
      <div class="cmd-tabs" role="tablist">
        <button
          v-for="tab in jpilotCommandTabs"
          :key="tab.id"
          type="button"
          role="tab"
          class="cmd-tab"
          :class="{ 'cmd-tab-active': selectedTab === tab.id }"
          :aria-selected="selectedTab === tab.id"
          @click="selectedTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="cmd-results-meta">
        <span class="cmd-results-label">Results</span>
        <span class="cmd-results-count">{{ flatResults.length }} actions</span>
      </div>
      <div class="cmd-results cmd-results-inline">
        <template v-for="group in groupedResults" :key="group.id">
          <div class="cmd-section-head">{{ group.title }}</div>
          <button
            v-for="cmd in group.commands.slice(0, inlinePerSection)"
            :key="cmd.id"
            type="button"
            class="cmd-result"
            :disabled="disabled && cmd.type === 'prompt'"
            @click="pickCommand(cmd)"
          >
            <span class="cmd-result-icon"><i :class="cmd.icon" /></span>
            <span class="cmd-result-body">
              <span class="cmd-result-title">{{ cmd.label }}</span>
              <span v-if="cmd.subtitle" class="cmd-result-sub">{{ cmd.subtitle }}</span>
            </span>
            <i v-if="cmd.type === 'link'" class="pi pi-arrow-right cmd-result-arrow" />
          </button>
        </template>
        <p v-if="!flatResults.length" class="cmd-empty">{{ emptyResultsHint }}</p>
      </div>
      <button type="button" class="cmd-show-all" @click="openMenu">
        Show all {{ flatResults.length }} actions by section
      </button>
    </div>

    <Dialog
      v-model:visible="dialogVisible"
      dismissable-mask
      modal
      :show-header="false"
      :draggable="false"
      :breakpoints="{ '1199px': '92vw', '767px': '96vw' }"
      :style="{ width: '60rem', maxWidth: '92vw' }"
      :content-style="{
        padding: 0,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        width: '100%'
      }"
      class="cmd-dialog"
      content-class="cmd-dialog-content"
      append-to="body"
      @hide="onDialogHide"
    >
      <div class="cmd-dialog-layout">
        <div class="cmd-dialog-main">
          <div class="cmd-dialog-search">
            <IconField icon-position="left" class="cmd-search-field">
              <InputIcon class="pi pi-search" />
              <InputText
                ref="searchInputRef"
                v-model="searchQuery"
                type="text"
                placeholder="Search prompts, architecture examples, tools…"
                class="cmd-search-input"
                @keydown.down.prevent="moveSelection(1)"
                @keydown.up.prevent="moveSelection(-1)"
                @keydown.enter.prevent="runSelected()"
              />
            </IconField>
            <span class="cmd-kbd">⌘K</span>
          </div>

          <div class="cmd-tabs cmd-tabs-dialog" role="tablist">
            <button
              v-for="tab in jpilotCommandTabs"
              :key="tab.id"
              type="button"
              role="tab"
              class="cmd-tab"
              :class="{ 'cmd-tab-active': selectedTab === tab.id }"
              @click="selectedTab = tab.id"
            >
              {{ tab.label }}
            </button>
          </div>

          <div class="cmd-dialog-body">
            <div class="cmd-dialog-results-column">
              <div class="cmd-results-meta cmd-results-meta-dialog">
                <span class="cmd-results-label">Results by section</span>
                <span class="cmd-results-count">{{ flatResults.length }} actions</span>
              </div>

              <div class="cmd-results cmd-results-dialog" ref="resultsEl">
                <template v-for="group in groupedResults" :key="group.id">
                  <div class="cmd-section-head cmd-section-head-dialog">
                    {{ group.title }}
                    <span class="cmd-section-count">{{ group.commands.length }}</span>
                  </div>
                  <button
                    v-for="cmd in group.commands"
                    :key="cmd.id"
                    type="button"
                    class="cmd-result"
                    :class="{ 'cmd-result-active': flatIndex(cmd.id) === selectedIndex }"
                    :disabled="disabled && cmd.type === 'prompt'"
                    @click="pickCommand(cmd)"
                    @mouseenter="selectedIndex = flatIndex(cmd.id)"
                  >
                    <span class="cmd-result-icon"><i :class="cmd.icon" /></span>
                    <span class="cmd-result-body">
                      <span class="cmd-result-title">{{ cmd.label }}</span>
                      <span v-if="cmd.subtitle" class="cmd-result-sub">{{ cmd.subtitle }}</span>
                    </span>
                    <i v-if="cmd.type === 'link'" class="pi pi-arrow-right cmd-result-arrow" />
                  </button>
                </template>
                <p v-if="!flatResults.length" class="cmd-empty">{{ emptyResultsHint }}</p>
              </div>
            </div>

            <aside class="cmd-dialog-sidebar" aria-label="Filter by section">
              <div v-for="(section, si) in commandSidebar" :key="si" class="cmd-sidebar-section">
                <h5 class="cmd-sidebar-title">{{ section.title }}</h5>
                <button
                  v-for="item in section.items"
                  :key="item.id"
                  type="button"
                  class="cmd-sidebar-link"
                  :class="{ 'cmd-sidebar-link-active': filterTag === item.id }"
                  @click="toggleFilter(item.id)"
                >
                  {{ item.label }}
                </button>
              </div>
            </aside>
          </div>
        </div>

        <div class="cmd-dialog-footer">
          <span class="cmd-footer-keys">
            <i class="pi pi-chevron-up" />
            <i class="pi pi-chevron-down" />
          </span>
          <p class="cmd-footer-hint">
            <span class="cmd-footer-accent">↑↓</span> navigate ·
            <span class="cmd-footer-accent">Enter</span> run ·
            <span class="cmd-footer-accent">Esc</span> close · sidebar filters one section
          </p>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import {
  defaultCommandTabForRole,
  getGroupedCommandResults,
  getJpilotCommandSidebar,
  jpilotCommandTabs
} from '../config/jpilotRecommendedActions'

const props = defineProps({
  activeRole: { type: String, default: 'operator' },
  /** When set (appliance selected), only show actions for this vendor. */
  applianceVendor: { type: String, default: null },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['pick'])

const dialogVisible = ref(false)
const searchQuery = ref('')
const selectedTab = ref('all')
const filterTag = ref(null)
const selectedIndex = ref(0)
const searchInputRef = ref(null)
const resultsEl = ref(null)

/** Inline list only renders on desktop (see CSS); show more rows there. */
const inlinePerSection = 5

const filterOpts = computed(() => ({
  tab: selectedTab.value,
  filterTag: filterTag.value,
  query: searchQuery.value,
  vendor: props.applianceVendor || null
}))

const commandSidebar = computed(() =>
  getJpilotCommandSidebar({
    tab: selectedTab.value,
    vendor: props.applianceVendor || null
  })
)

const groupedResults = computed(() => getGroupedCommandResults(filterOpts.value))

const flatResults = computed(() => groupedResults.value.flatMap((g) => g.commands))

const emptyResultsHint = computed(() => {
  if (props.applianceVendor) {
    return 'No recommended actions for this appliance vendor on this tab. Try another role tab or clear the appliance filter.'
  }
  return 'No actions match this tab.'
})

function flatIndex(cmdId) {
  return flatResults.value.findIndex((c) => c.id === cmdId)
}

watch([selectedTab, filterTag, searchQuery], () => {
  selectedIndex.value = 0
})

watch(
  () => props.applianceVendor,
  () => {
    filterTag.value = null
    selectedIndex.value = 0
  }
)

watch(
  () => props.activeRole,
  (role) => {
    selectedTab.value = defaultCommandTabForRole(role)
  },
  { immediate: true }
)

function openMenu() {
  dialogVisible.value = true
  nextTick(() => searchInputRef.value?.$el?.focus?.() || searchInputRef.value?.focus?.())
}

function onDialogHide() {
  searchQuery.value = ''
  filterTag.value = null
  selectedIndex.value = 0
}

function toggleFilter(id) {
  filterTag.value = filterTag.value === id ? null : id
}

function pickCommand(cmd) {
  dialogVisible.value = false
  emit('pick', cmd)
}

function moveSelection(delta) {
  const len = flatResults.value.length
  if (!len) return
  selectedIndex.value = (selectedIndex.value + delta + len) % len
  scrollSelectedIntoView()
}

function scrollSelectedIntoView() {
  nextTick(() => {
    const el = resultsEl.value?.querySelector('.cmd-result-active')
    el?.scrollIntoView({ block: 'nearest' })
  })
}

function runSelected() {
  const cmd = flatResults.value[selectedIndex.value]
  if (cmd) pickCommand(cmd)
}

function onGlobalKeydown(event) {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    if (dialogVisible.value) {
      dialogVisible.value = false
    } else {
      openMenu()
    }
  }
}

onMounted(() => window.addEventListener('keydown', onGlobalKeydown))
onUnmounted(() => window.removeEventListener('keydown', onGlobalKeydown))

defineExpose({ openMenu })
</script>

<style scoped>
.cmd-menu {
  margin-top: 1rem;
}

.cmd-menu-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.55rem 0.75rem;
  border: 1px dashed var(--glass-border);
  border-radius: 0.65rem;
  background: var(--glass-field);
  color: var(--glass-muted);
  font-size: 0.875rem;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.cmd-menu-trigger:hover:not(:disabled) {
  border-color: var(--p-primary-color);
  color: var(--glass-text);
}

.cmd-menu-trigger:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.cmd-kbd {
  margin-left: auto;
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  border: 1px solid var(--glass-border);
  border-radius: 0.35rem;
  color: var(--glass-muted);
}

.cmd-inline {
  margin-top: 0.75rem;
}

.cmd-tabs {
  display: flex;
  flex-shrink: 0;
  border-bottom: 1px solid var(--glass-border);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.cmd-tabs::-webkit-scrollbar {
  display: none;
}

.cmd-tab {
  flex: 0 0 auto;
  padding: 0.65rem 0.75rem;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--glass-muted);
  font-size: 0.8125rem;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.cmd-tab:hover {
  color: var(--glass-text);
}

.cmd-tab-active {
  color: var(--glass-text);
  border-bottom-color: var(--p-primary-color);
}

.cmd-results-meta {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.6rem 0.5rem 0.25rem;
}

.cmd-results-label {
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--glass-muted);
}

.cmd-results-count {
  font-size: 0.75rem;
  color: var(--glass-muted);
}

.cmd-section-head {
  padding: 0.65rem 0.5rem 0.25rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--p-primary-color);
  letter-spacing: 0.02em;
}

.cmd-section-count {
  margin-left: 0.35rem;
  font-weight: 600;
  color: var(--glass-muted);
}

.cmd-results {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}

.cmd-results-inline {
  max-height: min(22rem, 42vh);
  overflow-y: auto;
}

@media (min-width: 992px) {
  .cmd-inline {
    padding: 0.25rem 0.15rem 0;
  }

  .cmd-results-inline {
    max-height: min(34rem, 58vh);
    padding-right: 0.35rem;
  }

  .cmd-result {
    padding: 0.7rem 0.75rem;
    gap: 0.85rem;
  }

  .cmd-result-icon {
    width: 2.5rem;
    height: 2.5rem;
  }

  .cmd-result-title {
    font-size: 0.9375rem;
  }

  .cmd-result-sub {
    font-size: 0.8125rem;
    line-height: 1.45;
  }

  .cmd-section-head {
    padding: 0.85rem 0.75rem 0.35rem;
    font-size: 0.8125rem;
  }

  .cmd-tabs .cmd-tab {
    padding: 0.75rem 1rem;
  }
}

.cmd-results-dialog {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-bottom: 0.5rem;
}

.cmd-result {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.55rem 0.5rem;
  border: 0;
  border-radius: 0.55rem;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: background 0.12s;
}

.cmd-result:hover:not(:disabled),
.cmd-result-active {
  background: var(--glass-field);
}

.cmd-result:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cmd-result-icon {
  width: 2.25rem;
  height: 2.25rem;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--glass-border);
  border-radius: 0.55rem;
  color: var(--p-primary-color);
}

.cmd-result-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  overflow: hidden;
}

.cmd-result-title,
.cmd-result-sub {
  overflow-wrap: anywhere;
}

.cmd-result-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--glass-text);
  line-height: 1.3;
}

.cmd-result-sub {
  font-size: 0.75rem;
  color: var(--glass-muted);
  line-height: 1.35;
}

.cmd-result-arrow {
  color: var(--glass-muted);
  font-size: 0.8rem;
}

.cmd-empty {
  margin: 0.5rem;
  font-size: 0.8125rem;
  color: var(--glass-muted);
}

.cmd-show-all {
  margin-top: 0.5rem;
  padding: 0.35rem 0.5rem;
  border: 0;
  background: transparent;
  color: var(--p-primary-color);
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
}

.cmd-show-all:hover {
  text-decoration: underline;
}

:global(.p-dialog.cmd-dialog) {
  width: 60rem !important;
  max-width: 92vw !important;
  min-width: min(42rem, 92vw) !important;
  border: none !important;
  border-radius: 0.85rem !important;
  overflow: hidden !important;
  background: color-mix(in srgb, var(--p-surface-900) 88%, transparent) !important;
  backdrop-filter: blur(20px);
  box-shadow: 0 24px 64px rgb(0 0 0 / 45%) !important;
}

@media (max-width: 767px) {
  :global(.p-dialog.cmd-dialog) {
    min-width: 0 !important;
    width: 96vw !important;
    max-width: 96vw !important;
  }
}

:global(.p-dialog.cmd-dialog .p-dialog-content),
:global(.p-dialog.cmd-dialog .cmd-dialog-content) {
  padding: 0 !important;
  background: transparent !important;
  display: flex !important;
  flex-direction: column !important;
  width: 100% !important;
  max-height: min(90dvh, 42rem) !important;
  overflow: hidden !important;
}

@media (min-width: 992px) {
  :global(.p-dialog.cmd-dialog .p-dialog-content),
  :global(.p-dialog.cmd-dialog .cmd-dialog-content) {
    max-height: min(90dvh, 52rem) !important;
  }
}

:global(.p-dialog.cmd-dialog) .cmd-dialog-layout {
  display: flex;
  flex-direction: column;
  flex: 1;
  width: 100%;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

:global(.p-dialog.cmd-dialog) .cmd-dialog-main {
  flex: 1;
  width: 100%;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:global(.p-dialog.cmd-dialog) .cmd-dialog-body {
  flex: 1;
  min-height: 0;
  min-width: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

:global(.p-dialog.cmd-dialog) .cmd-dialog-results-column {
  flex: 1 1 auto;
  min-height: 0;
  min-width: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

@media (min-width: 768px) {
  :global(.p-dialog.cmd-dialog) .cmd-dialog-body {
    flex-direction: row;
    align-items: stretch;
  }
}

:global(.p-dialog.cmd-dialog) .cmd-dialog-sidebar {
  flex: 0 0 auto;
  width: 100%;
  max-height: 11rem;
  box-sizing: border-box;
  display: block;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 0.35rem 0 0.5rem;
  border-bottom: 1px solid color-mix(in srgb, var(--p-surface-0) 15%, transparent);
  background: color-mix(in srgb, var(--p-surface-900) 88%, transparent);
}

@media (min-width: 768px) {
  :global(.p-dialog.cmd-dialog) .cmd-dialog-sidebar {
    flex: 0 0 14rem;
    width: 14rem;
    max-width: 14rem;
    max-height: none;
    padding: 0.85rem 0;
    border-bottom: 0;
    border-left: 1px solid color-mix(in srgb, var(--p-surface-0) 15%, transparent);
  }
}

:global(.p-dialog.cmd-dialog) .cmd-sidebar-section {
  display: block;
  width: 100%;
  box-sizing: border-box;
}

:global(.p-dialog.cmd-dialog) .cmd-sidebar-section + .cmd-sidebar-section {
  margin-top: 0.55rem;
  padding-top: 0.55rem;
  border-top: 1px solid color-mix(in srgb, var(--p-surface-0) 10%, transparent);
}

:global(.p-dialog.cmd-dialog) .cmd-sidebar-title {
  display: block;
  margin: 0;
  padding: 0.35rem 1rem 0.3rem;
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: color-mix(in srgb, var(--p-surface-0) 40%, transparent);
  line-height: 1.3;
}

:global(.p-dialog.cmd-dialog) .cmd-sidebar-link {
  display: block;
  width: 100%;
  box-sizing: border-box;
  margin: 0;
  padding: 0.42rem 1rem;
  border: 0;
  border-radius: 0;
  background: transparent;
  text-align: left;
  font-size: 0.8125rem;
  line-height: 1.35;
  white-space: normal;
  overflow-wrap: anywhere;
  color: color-mix(in srgb, var(--p-surface-0) 70%, transparent);
  cursor: pointer;
  transition: color 0.12s, background 0.12s;
}

:global(.p-dialog.cmd-dialog) .cmd-sidebar-link:hover,
:global(.p-dialog.cmd-dialog) .cmd-sidebar-link-active {
  color: var(--p-surface-0);
  background: color-mix(in srgb, var(--p-surface-0) 8%, transparent);
}

.cmd-dialog-search {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  flex-shrink: 0;
}

.cmd-search-field {
  flex: 1;
}

:deep(.cmd-search-input) {
  width: 100% !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  color: var(--p-surface-0) !important;
}

:deep(.cmd-search-input::placeholder) {
  color: color-mix(in srgb, var(--p-surface-0) 55%, transparent) !important;
}

:deep(.cmd-search-field .p-inputicon) {
  color: color-mix(in srgb, var(--p-surface-0) 65%, transparent);
}

.cmd-tabs-dialog {
  flex-shrink: 0;
  border-top: 1px solid color-mix(in srgb, var(--p-surface-0) 15%, transparent);
  border-bottom: 1px solid color-mix(in srgb, var(--p-surface-0) 15%, transparent);
}

.cmd-tabs-dialog .cmd-tab {
  color: color-mix(in srgb, var(--p-surface-0) 65%, transparent);
}

.cmd-tabs-dialog .cmd-tab-active {
  color: var(--p-surface-0);
}

.cmd-results-meta-dialog {
  padding-left: 1rem;
  padding-right: 1rem;
  flex-shrink: 0;
}

.cmd-results-meta-dialog .cmd-results-label,
.cmd-results-meta-dialog .cmd-results-count {
  color: color-mix(in srgb, var(--p-surface-0) 55%, transparent);
}

.cmd-section-head-dialog {
  padding-left: 1rem;
  color: color-mix(in srgb, var(--p-primary-300) 90%, white);
}

:global(.p-dialog.cmd-dialog) .cmd-dialog-main .cmd-result {
  padding: 0.7rem 1rem;
  gap: 0.85rem;
}

:global(.p-dialog.cmd-dialog) .cmd-dialog-main .cmd-result-body {
  min-width: 0;
}

:global(.p-dialog.cmd-dialog) .cmd-dialog-main .cmd-result-title {
  white-space: normal;
  overflow-wrap: anywhere;
}

:global(.p-dialog.cmd-dialog) .cmd-dialog-main .cmd-result-sub {
  white-space: normal;
  overflow-wrap: anywhere;
}

.cmd-dialog-main .cmd-result-title {
  color: var(--p-surface-0);
}

.cmd-dialog-main .cmd-result-sub {
  color: color-mix(in srgb, var(--p-surface-0) 55%, transparent);
}

.cmd-dialog-main .cmd-result-icon {
  border-color: color-mix(in srgb, var(--p-surface-0) 20%, transparent);
}

.cmd-dialog-main .cmd-result:hover:not(:disabled),
.cmd-dialog-main .cmd-result-active {
  background: color-mix(in srgb, var(--p-surface-0) 10%, transparent);
}

.cmd-dialog-footer {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid color-mix(in srgb, var(--p-surface-0) 15%, transparent);
  flex-shrink: 0;
}

@media (max-width: 767px) {
  .cmd-dialog-footer {
    display: none;
  }

  .cmd-dialog-search .cmd-kbd {
    display: none;
  }
}

.cmd-footer-keys {
  display: flex;
  gap: 0.35rem;
  color: var(--p-surface-0);
  font-size: 0.75rem;
}

.cmd-footer-hint {
  margin: 0;
  font-size: 0.75rem;
  color: color-mix(in srgb, var(--p-surface-0) 55%, transparent);
  line-height: 1.4;
}

.cmd-footer-accent {
  color: var(--p-surface-0);
  font-weight: 600;
}

@media (max-width: 991px) {
  .cmd-inline {
    display: none;
  }

  .cmd-menu-trigger .cmd-kbd {
    display: none;
  }
}
</style>
