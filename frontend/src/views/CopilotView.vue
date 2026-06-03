<template>
  <div class="page copilot-page flex flex-column">
    <PageHeader title="JPilot" :subtitle="subtitle">
      <template #actions>
        <SelectButton
          v-model="windowCount"
          :options="windowOptions"
          option-label="label"
          option-value="value"
          :allow-empty="false"
          :disabled="!ready"
          v-tooltip.bottom="'Number of chat windows'"
        />
        <Button
          v-if="windowCount === 2"
          v-tooltip.bottom="orientation === 'horizontal' ? 'Stack vertically' : 'Place side by side'"
          :icon="orientation === 'horizontal' ? 'pi pi-arrows-v' : 'pi pi-arrows-h'"
          text
          rounded
          @click="toggleOrientation"
        />
        <div class="bg-picker-wrap">
          <Button v-tooltip.bottom="'Background'" icon="pi pi-image" text rounded @click="bgPickerOpen = !bgPickerOpen" />
          <div v-if="bgPickerOpen" class="bg-picker">
            <button
              v-for="bg in backgrounds"
              :key="bg.id"
              class="bg-thumb"
              :class="{ 'bg-thumb-active': background === bg.url }"
              :style="{ backgroundImage: `url(${bg.url})` }"
              @click="chooseBackground(bg.url)"
            />
            <button
              class="bg-thumb bg-thumb-none"
              :class="{ 'bg-thumb-active': background === 'none' }"
              @click="chooseBackground('none')"
            >
              None
            </button>
          </div>
        </div>
        <Button v-tooltip.top="'Chat settings'" icon="pi pi-cog" text rounded @click="router.push('/settings?section=jpilot')" />
      </template>
    </PageHeader>

    <Message v-if="!ready" severity="warn" :closable="false" class="mb-3">
      No enabled AI provider found.
      <RouterLink to="/settings?section=ai-providers" class="ml-2">Configure AI Providers →</RouterLink>
    </Message>

    <div class="stage flex-1" :style="stageStyle">
      <div class="stage-scrim" />
      <div class="panes-wrap" :class="orientation === 'vertical' ? 'panes-vertical' : 'panes-horizontal'">
        <ChatPane
          class="pane-slot"
          session-id="pane-1"
          :providers="providers"
          :appliances="appliances"
          :default-provider-id="defaultProviderId"
          :web-search-available="webSearchAvailable"
          :can-close="windowCount === 2"
          @close="windowCount = 1"
        />

        <div
          v-if="windowCount === 2"
          class="pane-divider"
          :class="orientation === 'vertical' ? 'divider-horizontal' : 'divider-vertical'"
        >
          <span class="divider-line" />
          <span class="divider-chip"><i class="pi pi-sparkles" /></span>
          <span class="divider-line" />
        </div>

        <ChatPane
          v-if="windowCount === 2"
          class="pane-slot"
          session-id="pane-2"
          :providers="providers"
          :appliances="appliances"
          :default-provider-id="defaultProviderId"
          :web-search-available="webSearchAvailable"
          :can-close="true"
          @close="windowCount = 1"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Message from 'primevue/message'
import SelectButton from 'primevue/selectbutton'
import PageHeader from '../components/PageHeader.vue'
import ChatPane from '../components/ChatPane.vue'
import {
  CHAT_BACKGROUNDS,
  getChatBackground,
  listChatProviders,
  listCopilotAppliances,
  setChatBackground
} from '../services/copilot'
import { getCopilotPlatformSettings } from '../services/copilotPlatform'

const router = useRouter()

const providers = ref([])
const appliances = ref([])
const orientation = ref('horizontal')
const windowCount = ref(1)
const windowOptions = [
  { label: '1', value: 1 },
  { label: '2', value: 2 }
]
const backgrounds = CHAT_BACKGROUNDS
const background = ref(getChatBackground())
const bgPickerOpen = ref(false)
const webSearchAvailable = ref(false)

const ready = computed(() => providers.value.length > 0)

const defaultProviderId = computed(() => {
  const def = providers.value.find((p) => p.isDefault)
  return (def || providers.value[0])?.id || ''
})

const subtitle = computed(() => {
  if (!ready.value) return 'Configure an AI provider to start'
  if (windowCount.value > 1) return 'Two chats · pick a model and appliance per chat'
  const def = providers.value.find((p) => p.isDefault) || providers.value[0]
  return def ? `${def.providerName} · ${def.model}` : ''
})

const stageStyle = computed(() =>
  background.value === 'none' ? {} : { backgroundImage: `url(${background.value})` }
)

function toggleOrientation() {
  orientation.value = orientation.value === 'horizontal' ? 'vertical' : 'horizontal'
}

function chooseBackground(url) {
  background.value = url
  setChatBackground(url)
  bgPickerOpen.value = false
}

async function loadProviders() {
  try {
    providers.value = await listChatProviders()
  } catch {
    providers.value = []
  }
}

async function loadAppliances() {
  try {
    appliances.value = await listCopilotAppliances()
  } catch {
    appliances.value = []
  }
}

async function loadWebSearchAvailability() {
  try {
    const settings = await getCopilotPlatformSettings()
    webSearchAvailable.value = !!(settings.allowWebSearch && settings.hasBraveSearchApiKey)
  } catch {
    webSearchAvailable.value = false
  }
}

onMounted(() => {
  loadProviders()
  loadAppliances()
  loadWebSearchAvailability()
})
</script>

<style scoped>
.copilot-page {
  height: calc(100vh - 3rem);
  min-height: 32rem;
}

.stage {
  position: relative;
  border-radius: 1rem;
  overflow: hidden;
  background-color: var(--p-surface-100);
  background-size: cover;
  background-position: center;
  min-height: 0;
}

:global(.app-dark) .stage {
  background-color: var(--p-surface-950);
}

.stage-scrim {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.35);
  pointer-events: none;
}

:global(.app-dark) .stage-scrim {
  background: rgba(2, 6, 23, 0.55);
}

.panes-wrap {
  position: relative;
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  height: 100%;
  min-height: 0;
}

.panes-horizontal {
  flex-direction: row;
}

.panes-vertical {
  flex-direction: column;
}

.pane-slot {
  flex: 1 1 0;
  min-height: 0;
  min-width: 0;
}

/* Centered-content divider between the two panes */
.pane-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.divider-vertical {
  flex-direction: column;
  width: 1.5rem;
}

.divider-horizontal {
  flex-direction: row;
  height: 1.5rem;
}

.divider-line {
  background: var(--p-content-border-color);
}

.divider-vertical .divider-line {
  width: 1px;
  flex: 1;
}

.divider-horizontal .divider-line {
  height: 1px;
  flex: 1;
}

.divider-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.6rem;
  height: 1.6rem;
  margin: 0.4rem;
  border-radius: 999px;
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  color: var(--p-primary-color);
  font-size: 0.8rem;
}

.bg-picker-wrap {
  position: relative;
}

.bg-picker {
  position: absolute;
  right: 0;
  top: 2.75rem;
  z-index: 20;
  display: grid;
  grid-template-columns: repeat(2, 4.5rem);
  gap: 0.5rem;
  padding: 0.6rem;
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: 0.75rem;
  box-shadow: 0 12px 32px rgba(2, 6, 23, 0.2);
}

.bg-thumb {
  width: 4.5rem;
  height: 3rem;
  border-radius: 0.5rem;
  border: 2px solid transparent;
  background-size: cover;
  background-position: center;
  cursor: pointer;
  color: var(--p-text-muted-color);
  font-size: 0.75rem;
}

.bg-thumb-none {
  background: var(--p-surface-100);
  display: flex;
  align-items: center;
  justify-content: center;
}

.bg-thumb-active {
  border-color: var(--p-primary-color);
}
</style>
