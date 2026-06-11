<template>
  <div class="install-block">
    <div class="install-terminal">
      <div class="terminal-bar">
        <span class="terminal-dot" />
        <span class="terminal-dot" />
        <span class="terminal-dot" />
        <span class="terminal-title">{{ activePlatform.terminalTitle }}</span>
      </div>
      <div class="install-terminal-body">
        <pre class="install-command"><code><span class="cmd-prompt">{{ activePlatform.prompt }} </span>{{ activePlatform.command }}</code></pre>
        <button
          type="button"
          class="install-copy-btn"
          :class="{ copied }"
          :aria-label="`Copy ${activePlatform.label} install command`"
          @click="copyCommand"
        >
          <i :class="copied ? 'pi pi-check' : 'pi pi-copy'" />
          {{ copied ? 'Copied' : 'Copy' }}
        </button>
      </div>
    </div>

    <div class="install-platform-tabs" role="tablist" aria-label="Install platform">
      <button
        v-for="platform in platforms"
        :key="platform.id"
        type="button"
        role="tab"
        class="install-platform-tab"
        :class="{ active: platform.id === activeId }"
        :aria-selected="platform.id === activeId"
        @click="activeId = platform.id"
      >
        <i :class="platform.icon" aria-hidden="true" />
        {{ platform.label }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const curlCommand = 'curl -fsSL https://install.nexxus-tech.com/jpilot | bash'
const windowsCommand = 'irm https://install.nexxus-tech.com/jpilot/ps1 | iex'

const platforms = [
  {
    id: 'macos',
    label: 'macOS',
    icon: 'pi pi-apple',
    prompt: '$',
    command: curlCommand,
    terminalTitle: 'Terminal · macOS'
  },
  {
    id: 'linux',
    label: 'Linux',
    icon: 'pi pi-desktop',
    prompt: '$',
    command: curlCommand,
    terminalTitle: 'Terminal · Linux'
  },
  {
    id: 'windows',
    label: 'Windows',
    icon: 'pi pi-microsoft',
    prompt: '>',
    command: windowsCommand,
    terminalTitle: 'PowerShell · Windows'
  }
]

const activeId = ref('macos')
const copied = ref(false)

const activePlatform = computed(
  () => platforms.find((platform) => platform.id === activeId.value) || platforms[0]
)

async function copyCommand() {
  try {
    await navigator.clipboard.writeText(activePlatform.value.command)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    copied.value = false
  }
}
</script>

<style scoped>
.install-block {
  width: 100%;
  max-width: 45rem;
  margin-inline: auto;
}

.install-terminal {
  text-align: left;
  background: #0b1220;
  border: 1px solid #1e293b;
  border-radius: 0.875rem;
  overflow: hidden;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.45);
  margin-bottom: 1rem;
}

.terminal-bar {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.75rem 1rem;
  background: rgba(0, 0, 0, 0.35);
  border-bottom: 1px solid #1e293b;
}

.terminal-dot {
  width: 0.625rem;
  height: 0.625rem;
  border-radius: 50%;
  background: #334155;
}

.terminal-dot:first-child {
  background: #ef4444;
}

.terminal-dot:nth-child(2) {
  background: #f59e0b;
}

.terminal-dot:nth-child(3) {
  background: #22c55e;
}

.terminal-title {
  margin-left: 0.5rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: #94a3b8;
  letter-spacing: 0.04em;
}

.install-terminal-body {
  display: flex;
  align-items: stretch;
}

.install-command {
  flex: 1;
  min-width: 0;
  margin: 0;
  padding: 1rem 1.125rem;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  background: #020617;
}

.install-command code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace;
  font-size: clamp(0.72rem, 2.5vw, 0.84rem);
  line-height: 1.65;
  color: #e2e8f0;
  white-space: pre-wrap;
  word-break: break-all;
}

.cmd-prompt {
  color: var(--p-primary-400);
  user-select: none;
}

.install-copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 1rem 1.125rem;
  border: none;
  border-left: 1px solid #1e293b;
  border-radius: 0;
  background: #1e293b;
  color: #cbd5e1;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  transition: border-color 0.2s ease, color 0.2s ease, background 0.2s ease;
  flex-shrink: 0;
  align-self: stretch;
}

.install-copy-btn:hover {
  border-color: var(--p-primary-500);
  color: var(--p-primary-300);
}

.install-copy-btn.copied {
  border-color: rgba(34, 197, 94, 0.45);
  background: rgba(34, 197, 94, 0.12);
  color: #4ade80;
}

.install-platform-tabs {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

.install-platform-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  border-radius: 0.5rem;
  border: 1px solid color-mix(in srgb, var(--p-primary-400) 28%, transparent);
  background: rgba(0, 0, 0, 0.2);
  color: var(--landing-text-muted, var(--p-text-muted-color));
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.2s ease, color 0.2s ease, background 0.2s ease;
}

.install-platform-tab:hover,
.install-platform-tab.active {
  border-color: var(--p-primary-500);
  color: var(--p-primary-300);
  background: color-mix(in srgb, var(--p-primary-500) 16%, transparent);
}

@media (max-width: 767px) {
  .install-terminal-body {
    flex-direction: column;
  }

  .install-copy-btn {
    width: 100%;
    justify-content: center;
    border-left: none;
    border-top: 1px solid #1e293b;
    padding: 0.875rem;
    font-size: 0.82rem;
  }
}
</style>
