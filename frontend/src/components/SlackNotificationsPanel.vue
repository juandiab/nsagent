<template>
  <div class="slack-panel">
    <div v-if="loading" class="content-panel content-panel-padded py-4">
      <ProgressSpinner style="width: 2rem; height: 2rem" />
    </div>

    <div v-else class="content-panel content-panel-padded">
      <div class="flex align-items-start justify-content-between gap-3 flex-wrap">
        <div>
          <h2 class="section-title">Slack notifications</h2>
          <p class="section-copy">
            Route operational alerts and workflow updates to your team channels.
            Settings are stored in your JPilot database — enable delivery when you are ready.
          </p>
        </div>
        <Tag
          :value="statusTagLabel"
          :severity="statusTagSeverity"
          :icon="settings.enabled && settings.hasWebhookUrl ? 'pi pi-check-circle' : 'pi pi-bell'"
        />
      </div>

      <div class="flex align-items-center justify-content-between gap-3 setting-row mt-4">
        <div>
          <div class="setting-label">Enable Slack notifications</div>
          <div class="setting-hint">
            Send configured alerts to Slack when events occur.
          </div>
        </div>
        <ToggleSwitch v-model="form.enabled" />
      </div>

      <div class="slack-fields mt-4">
        <div class="flex flex-column gap-2 setting-row">
          <label for="slackWebhookUrl" class="setting-label">Incoming webhook URL</label>
          <InputText
            id="slackWebhookUrl"
            v-model="form.webhookUrl"
            placeholder="https://hooks.slack.com/services/…"
            autocomplete="off"
          />
          <small v-if="settings.hasWebhookUrl && !form.webhookUrl" class="setting-hint">
            Saved webhook: {{ settings.webhookUrlPreview }}. Enter a new URL to replace it.
          </small>
          <small v-else class="setting-hint">
            Create an incoming webhook in your Slack workspace and paste the URL here.
          </small>
        </div>

        <div class="flex flex-column gap-2 setting-row mt-3">
          <label for="slackDefaultChannel" class="setting-label">Default channel (optional)</label>
          <InputText
            id="slackDefaultChannel"
            v-model="form.defaultChannel"
            placeholder="#jpilot-alerts"
          />
          <small class="setting-hint">
            Override the webhook default channel. Use a channel name such as <code>#operations</code>.
          </small>
        </div>

        <div class="notification-types mt-4">
          <h3 class="subsection-title">Notification types</h3>
          <p class="setting-hint m-0 mt-1">
            Select which operational events will be routed to Slack once delivery is enabled.
          </p>

          <div class="flex align-items-center justify-content-between gap-3 setting-row mt-3">
            <div>
              <div class="setting-label">License and renewal alerts</div>
              <div class="setting-hint">Expiration warnings and renewal confirmations.</div>
            </div>
            <ToggleSwitch v-model="form.notifyLicenseAlerts" />
          </div>

          <div class="flex align-items-center justify-content-between gap-3 setting-row mt-3">
            <div>
              <div class="setting-label">Workflow updates</div>
              <div class="setting-hint">Copilot job completion and operational workflow status.</div>
            </div>
            <ToggleSwitch v-model="form.notifyWorkflowUpdates" />
          </div>

          <div class="flex align-items-center justify-content-between gap-3 setting-row mt-3">
            <div>
              <div class="setting-label">Security health checks</div>
              <div class="setting-hint">Scheduled hardening and health-check summaries.</div>
            </div>
            <ToggleSwitch v-model="form.notifyHealthChecks" />
          </div>
        </div>

        <div class="flex flex-column gap-2 setting-row mt-4">
          <label for="slackTestMessage" class="setting-label">Test message</label>
          <InputText
            id="slackTestMessage"
            v-model="testMessage"
            placeholder="JPilot Slack test notification."
          />
        </div>

        <div class="flex flex-wrap gap-2 pt-3">
          <Button
            label="Save Slack settings"
            icon="pi pi-save"
            size="small"
            :loading="saving"
            @click="saveSettings"
          />
          <Button
            label="Send test notification"
            icon="pi pi-send"
            size="small"
            severity="secondary"
            outlined
            :loading="testing"
            @click="sendTest"
          />
        </div>

        <Message v-if="message" class="mt-3" :severity="messageSeverity" :closable="false">
          {{ message }}
        </Message>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'
import { getSlackConfig, saveSlackConfig, testSlackConfig } from '../services/slack'

const loading = ref(true)
const saving = ref(false)
const testing = ref(false)
const message = ref('')
const messageSeverity = ref('info')
const testMessage = ref('JPilot Slack test notification.')

const settings = reactive({
  enabled: false,
  hasWebhookUrl: false,
  webhookUrlPreview: null,
  defaultChannel: '',
  notifyLicenseAlerts: true,
  notifyWorkflowUpdates: true,
  notifyHealthChecks: false
})

const form = reactive({
  enabled: false,
  webhookUrl: '',
  defaultChannel: '',
  notifyLicenseAlerts: true,
  notifyWorkflowUpdates: true,
  notifyHealthChecks: false
})

const statusTagLabel = computed(() => {
  if (settings.enabled && settings.hasWebhookUrl) return 'Active'
  if (settings.hasWebhookUrl) return 'Configured'
  return 'Not configured'
})

const statusTagSeverity = computed(() => {
  if (settings.enabled && settings.hasWebhookUrl) return 'success'
  if (settings.hasWebhookUrl) return 'info'
  return 'secondary'
})

function applySettings(data) {
  Object.assign(settings, {
    enabled: data.enabled,
    hasWebhookUrl: data.hasWebhookUrl,
    webhookUrlPreview: data.webhookUrlPreview,
    defaultChannel: data.defaultChannel || '',
    notifyLicenseAlerts: data.notifyLicenseAlerts ?? true,
    notifyWorkflowUpdates: data.notifyWorkflowUpdates ?? true,
    notifyHealthChecks: data.notifyHealthChecks ?? false
  })
  Object.assign(form, {
    enabled: data.enabled,
    webhookUrl: '',
    defaultChannel: data.defaultChannel || '',
    notifyLicenseAlerts: data.notifyLicenseAlerts ?? true,
    notifyWorkflowUpdates: data.notifyWorkflowUpdates ?? true,
    notifyHealthChecks: data.notifyHealthChecks ?? false
  })
}

function buildPayload() {
  return {
    enabled: form.enabled,
    webhookUrl: form.webhookUrl.trim() ? form.webhookUrl.trim() : null,
    defaultChannel: form.defaultChannel,
    notifyLicenseAlerts: form.notifyLicenseAlerts,
    notifyWorkflowUpdates: form.notifyWorkflowUpdates,
    notifyHealthChecks: form.notifyHealthChecks
  }
}

async function loadSettings() {
  loading.value = true
  message.value = ''
  try {
    applySettings(await getSlackConfig())
  } catch (error) {
    message.value = error.response?.data?.detail || 'Failed to load Slack settings'
    messageSeverity.value = 'error'
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  message.value = ''
  try {
    applySettings(await saveSlackConfig(buildPayload()))
    message.value = 'Slack settings saved.'
    messageSeverity.value = 'success'
  } catch (error) {
    message.value = error.response?.data?.detail || 'Failed to save Slack settings'
    messageSeverity.value = 'error'
  } finally {
    saving.value = false
  }
}

async function sendTest() {
  testing.value = true
  message.value = ''
  try {
    const result = await testSlackConfig({
      webhookUrl: form.webhookUrl.trim() || null,
      message: testMessage.value.trim()
    })
    message.value = result.message
    messageSeverity.value = result.success ? 'success' : 'error'
  } catch (error) {
    message.value = error.response?.data?.detail || 'Failed to send Slack test notification'
    messageSeverity.value = 'error'
  } finally {
    testing.value = false
  }
}

onMounted(loadSettings)
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

.subsection-title {
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0;
  color: var(--p-text-color);
}

.setting-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.setting-hint {
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
  line-height: 1.5;
}

.setting-row {
  max-width: 40rem;
}

.notification-types {
  padding-top: 0.25rem;
  border-top: 1px solid var(--p-content-border-color);
}
</style>
