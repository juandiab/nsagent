<template>
  <div class="content-panel content-panel-padded brave-search-panel h-full">
    <div class="panel-intro">
      <div class="panel-eyebrow">
        <Tag value="Search API" severity="secondary" icon="pi pi-globe" />
        <span>Not a language model</span>
      </div>
      <h2 class="section-title mt-2">Documentation web search</h2>
      <p class="section-copy">
        Brave Search is optional and separate from your LLM providers above.
        JPilot always uses the official NetScaler Next-Gen API guide from memory; enable Brave only when you
        want broader internet documentation results alongside that guide.
      </p>
    </div>

    <Message severity="info" :closable="false" class="mt-3 mb-0">
      Brave does not generate chat replies — it only retrieves web pages for JPilot to read when searching
      NetScaler or CLI documentation.
    </Message>

    <div class="flex flex-column gap-4 mt-4">
      <div class="flex align-items-center justify-content-between gap-3 setting-row">
        <div>
          <div class="setting-label">Enable Brave web search</div>
          <div class="setting-hint">Adds internet doc results on top of the built-in official guide search.</div>
        </div>
        <ToggleSwitch v-model="platformSettings.allowWebSearch" />
      </div>

      <div class="flex flex-column gap-2 setting-row">
        <label for="braveApiKey" class="setting-label">Brave Search API key</label>
        <Password
          id="braveApiKey"
          v-model="platformSettings.braveSearchApiKey"
          class="w-full"
          :feedback="false"
          toggle-mask
          input-class="w-full"
          :placeholder="platformSettings.hasBraveSearchApiKey ? 'Saved — enter a new key to replace' : 'BSA...'"
        />
        <small class="setting-hint">
          Get a key from <a href="https://brave.com/search/api/" target="_blank" rel="noopener">Brave Search API</a>.
          Stored encrypted on the backend. This key is not used for chat completions.
        </small>
      </div>

      <div class="flex flex-column gap-2 setting-row">
        <div class="setting-label">Allowed domains</div>
        <div class="setting-hint">
          Web search results are restricted to these domains. Official NetScaler/Citrix domains are always
          included; add internal doc sites below.
        </div>
        <div class="domain-chips">
          <span v-for="d in lockedDomains" :key="d" class="domain-chip domain-chip-locked">
            <i class="pi pi-lock" /> {{ d }}
          </span>
          <span v-for="d in platformSettings.extraDomains" :key="d" class="domain-chip">
            {{ d }}
            <button type="button" class="domain-remove" @click="removeDomain(d)">
              <i class="pi pi-times" />
            </button>
          </span>
        </div>
        <div class="flex gap-2">
          <InputText
            v-model="newDomain"
            class="flex-1"
            placeholder="e.g. docs.internal.example.com"
            @keydown.enter.prevent="addDomain"
          />
          <Button label="Add" icon="pi pi-plus" size="small" severity="secondary" outlined @click="addDomain" />
        </div>
        <small class="setting-hint">Remember to save after editing domains.</small>
      </div>

      <div class="flex gap-2 pt-2">
        <Button
          label="Save search settings"
          icon="pi pi-save"
          size="small"
          :loading="saving"
          @click="saveSettings"
        />
        <Button
          label="Test search"
          icon="pi pi-bolt"
          size="small"
          severity="secondary"
          outlined
          :loading="testing"
          @click="testSearch"
        />
      </div>

      <Message v-if="message" :severity="messageSeverity" :closable="false">
        {{ message }}
      </Message>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'
import {
  getCopilotPlatformSettings,
  saveCopilotPlatformSettings,
  testCopilotPlatformSearch
} from '../services/copilotPlatform'

const emit = defineEmits(['usage-changed'])

const saving = ref(false)
const testing = ref(false)
const message = ref('')
const messageSeverity = ref('info')
const platformSettings = reactive({
  allowWebSearch: false,
  hasBraveSearchApiKey: false,
  braveSearchApiKey: '',
  extraDomains: []
})
const lockedDomains = ref([])
const newDomain = ref('')

async function loadSettings() {
  try {
    const settings = await getCopilotPlatformSettings()
    Object.assign(platformSettings, {
      allowWebSearch: settings.allowWebSearch,
      hasBraveSearchApiKey: settings.hasBraveSearchApiKey,
      braveSearchApiKey: '',
      extraDomains: [...(settings.extraDomains || [])]
    })
    lockedDomains.value = settings.lockedDomains || []
  } catch (error) {
    message.value = error.response?.data?.detail || 'Failed to load Brave Search settings'
    messageSeverity.value = 'error'
  }
}

async function saveSettings() {
  saving.value = true
  message.value = ''
  try {
    const payload = {
      allowWebSearch: platformSettings.allowWebSearch,
      braveSearchApiKey: platformSettings.braveSearchApiKey || null,
      extraDomains: platformSettings.extraDomains
    }
    const saved = await saveCopilotPlatformSettings(payload)
    Object.assign(platformSettings, {
      allowWebSearch: saved.allowWebSearch,
      hasBraveSearchApiKey: saved.hasBraveSearchApiKey,
      braveSearchApiKey: '',
      extraDomains: [...(saved.extraDomains || [])]
    })
    lockedDomains.value = saved.lockedDomains || []
    message.value = 'Brave Search settings saved.'
    messageSeverity.value = 'success'
    emit('usage-changed')
  } catch (error) {
    message.value = error.response?.data?.detail || 'Failed to save Brave Search settings'
    messageSeverity.value = 'error'
  } finally {
    saving.value = false
  }
}

function addDomain() {
  let d = (newDomain.value || '').trim().toLowerCase()
  d = d.replace(/^https?:\/\//, '').split('/')[0].replace(/^\.+|\.+$/g, '')
  if (!d) return
  if (lockedDomains.value.includes(d) || platformSettings.extraDomains.includes(d)) {
    newDomain.value = ''
    return
  }
  platformSettings.extraDomains.push(d)
  newDomain.value = ''
}

function removeDomain(domain) {
  platformSettings.extraDomains = platformSettings.extraDomains.filter((d) => d !== domain)
}

async function testSearch() {
  testing.value = true
  message.value = ''
  try {
    const result = await testCopilotPlatformSearch({
      allowWebSearch: platformSettings.allowWebSearch,
      braveSearchApiKey: platformSettings.braveSearchApiKey || null
    })
    message.value = result.message
    messageSeverity.value = result.success ? 'success' : 'error'
    if (result.success) {
      emit('usage-changed')
    }
  } catch (error) {
    message.value = error.response?.data?.detail || 'Brave Search test failed'
    messageSeverity.value = 'error'
  } finally {
    testing.value = false
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.brave-search-panel {
  border-left: 3px solid var(--p-surface-400);
  background: var(--app-nested-surface);
}

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

.setting-row {
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--p-content-border-color);
}

.setting-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.setting-label {
  font-size: 0.9375rem;
  font-weight: 500;
}

.setting-hint {
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
  margin-top: 0.2rem;
}

.domain-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.domain-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  font-size: 0.8125rem;
  background: var(--app-nested-surface-strong);
  border: 1px solid var(--p-content-border-color);
}

.domain-chip-locked {
  color: var(--p-text-muted-color);
}

.domain-remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--p-text-muted-color);
  cursor: pointer;
  line-height: 1;
}

.domain-remove:hover {
  color: var(--p-text-color);
}
</style>
