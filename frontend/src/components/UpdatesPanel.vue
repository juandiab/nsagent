<template>
  <div class="updates-panel flex flex-column gap-4">
    <div class="content-panel content-panel-padded">
      <div class="flex align-items-start justify-content-between gap-3 flex-wrap">
        <div>
          <h2 class="section-title">About JPilot</h2>
          <p class="section-copy">
            Installed version and release checks against GitHub.
          </p>
        </div>
        <Tag :value="updateInfo?.display_version || '…'" severity="secondary" />
      </div>

      <div v-if="loading" class="mt-4">
        <ProgressSpinner style="width: 2rem; height: 2rem" />
      </div>

      <div v-else class="flex flex-column gap-4 mt-4">
        <Message
          v-if="updateInfo?.update_available"
          severity="warn"
          :closable="false"
        >
          <span>
            <strong>{{ updateInfo.latest_display_version }}</strong> is available
            (you are on {{ updateInfo.display_version }}).
            <a
              v-if="updateInfo.release_url"
              :href="updateInfo.release_url"
              target="_blank"
              rel="noopener noreferrer"
              class="release-link"
            >View release notes</a>
          </span>
        </Message>

        <Message
          v-else-if="updateInfo && !updateInfo.check_error"
          severity="success"
          :closable="false"
        >
          You are on the latest release.
        </Message>

        <Message
          v-if="updateInfo?.check_error"
          severity="info"
          :closable="false"
        >
          {{ updateInfo.check_error }} You can try again later.
        </Message>

        <div class="flex gap-2 flex-wrap">
          <Button
            label="Check for updates"
            icon="pi pi-refresh"
            size="small"
            :loading="checking"
            @click="runCheck(true)"
          />
          <span v-if="lastCheckedLabel" class="checked-at">{{ lastCheckedLabel }}</span>
        </div>
      </div>
    </div>

    <div
      v-if="updateInfo?.update_available"
      class="content-panel content-panel-padded"
    >
      <h2 class="section-title">How to update</h2>
      <p class="section-copy">{{ updateInfo.update_instructions.summary }}</p>

      <ol class="update-steps mt-4">
        <li v-for="(step, index) in updateInfo.update_instructions.steps" :key="index">
          {{ step }}
        </li>
      </ol>

      <p class="section-copy mt-4">
        From the repository root, run the upgrade helper. It pulls <code>origin/main</code>, asks
        whether to rebuild the <strong>development</strong> or <strong>production</strong> stack, then runs
        <code>docker compose build</code> and <code>up -d</code>. Your <code>.env</code> and MongoDB data
        are kept.
      </p>

      <div class="install-grid mt-4">
        <div class="command-block">
          <div class="command-label">macOS / Linux</div>
          <pre class="command-pre"><code>{{ upgradeLinuxCommands }}</code></pre>
          <Button
            label="Copy"
            icon="pi pi-copy"
            size="small"
            severity="secondary"
            outlined
            class="mt-2"
            @click="copyCommands(upgradeLinuxCommands)"
          />
        </div>

        <div class="command-block">
          <div class="command-label">Windows (PowerShell)</div>
          <pre class="command-pre"><code>{{ upgradeWindowsCommands }}</code></pre>
          <Button
            label="Copy"
            icon="pi pi-copy"
            size="small"
            severity="secondary"
            outlined
            class="mt-2"
            @click="copyCommands(upgradeWindowsCommands)"
          />
        </div>
      </div>

      <p class="section-copy mt-4">
        Alternatively, re-run the bootstrap installer from the project README on the host;
        it updates an existing checkout and rebuilds the stack.
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'
import { checkForUpdates } from '../services/system'

const emit = defineEmits(['update-status'])

const loading = ref(true)
const checking = ref(false)
const updateInfo = ref(null)

const upgradeLinuxCommands = './scripts/upgrade.sh'
const upgradeWindowsCommands = '.\\scripts\\upgrade.ps1'

const lastCheckedLabel = computed(() => {
  if (!updateInfo.value?.checked_at) return ''
  const when = new Date(updateInfo.value.checked_at)
  if (Number.isNaN(when.getTime())) return ''
  return `Last checked ${when.toLocaleString()}`
})

async function runCheck(force = false) {
  checking.value = true
  try {
    updateInfo.value = await checkForUpdates(force)
    emit('update-status', updateInfo.value)
  } catch (error) {
    updateInfo.value = {
      display_version: updateInfo.value?.display_version || 'unknown',
      check_error: error.response?.data?.detail || 'Could not check for updates.',
      update_available: false,
      update_instructions: { summary: '', steps: [], commands_linux_mac: [], commands_windows: [] }
    }
  } finally {
    checking.value = false
    loading.value = false
  }
}

async function copyCommands(text) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    // Clipboard may be blocked; ignore.
  }
}

onMounted(() => runCheck(false))

defineExpose({ refresh: () => runCheck(true) })
</script>

<style scoped>
.updates-panel {
  width: 100%;
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
  line-height: 1.55;
}

.section-copy code {
  font-size: 0.8125rem;
}

.release-link {
  margin-left: 0.35rem;
  color: inherit;
  font-weight: 600;
}

.checked-at {
  align-self: center;
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
}

.update-steps {
  margin: 0;
  padding-left: 1.25rem;
  color: var(--p-text-color);
  line-height: 1.6;
  font-size: 0.875rem;
}

.update-steps li + li {
  margin-top: 0.5rem;
}

.install-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  align-items: start;
}

@media (max-width: 991px) {
  .install-grid {
    grid-template-columns: 1fr;
  }
}

.command-block {
  padding: 1rem;
  border-radius: 0.75rem;
  border: 1px solid var(--p-content-border-color);
  background: var(--app-nested-surface, var(--p-surface-100));
}

.command-label {
  font-size: 0.8125rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.command-hint {
  margin: 0;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  line-height: 1.45;
}

.command-hint code {
  font-size: 0.6875rem;
}

.command-pre {
  margin: 0;
  padding: 0.75rem;
  border-radius: 0.5rem;
  background: color-mix(in srgb, var(--p-surface-950) 6%, transparent);
  overflow-x: auto;
  font-size: 0.8125rem;
  line-height: 1.5;
}

:global(.app-dark) .command-pre {
  background: rgba(0, 0, 0, 0.25);
}
</style>
