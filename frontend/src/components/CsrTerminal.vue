<template>
  <div class="csr-terminal">
    <div class="csr-terminal__header">
      <span class="csr-terminal__title">
        <i class="pi pi-terminal" aria-hidden="true" />
        {{ title }}
      </span>
      <Button
        :label="copyLabel"
        icon="pi pi-copy"
        size="small"
        severity="secondary"
        :disabled="!pem"
        @click="copyPem"
      />
    </div>
    <pre class="csr-terminal__body"><code>{{ pem || placeholder }}</code></pre>
    <p v-if="copied" class="csr-terminal__hint">Copied to clipboard.</p>
    <div v-if="paths.length" class="csr-terminal__paths">
      <div v-for="item in paths" :key="item.label" class="path-row">
        <span class="path-label">{{ item.label }}</span>
        <code>{{ item.value }}</code>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import Button from 'primevue/button'

const props = defineProps({
  title: { type: String, default: 'Output' },
  copyLabel: { type: String, default: 'Copy PEM' },
  pem: { type: String, default: '' },
  keyPath: { type: String, default: '' },
  csrPath: { type: String, default: '' },
  certPath: { type: String, default: '' },
  reqPath: { type: String, default: '' },
  certKeyName: { type: String, default: '' },
  placeholder: {
    type: String,
    default: 'Generated PEM output will appear here.'
  }
})

const copied = ref(false)

const paths = computed(() => {
  const items = []
  if (props.keyPath) items.push({ label: 'Private key', value: props.keyPath })
  if (props.reqPath) items.push({ label: 'CSR request file', value: props.reqPath })
  if (props.csrPath) items.push({ label: 'CSR file', value: props.csrPath })
  if (props.certPath) items.push({ label: 'Certificate file', value: props.certPath })
  if (props.certKeyName) {
    items.push({
      label: 'certKey name (use for bind ssl vserver)',
      value: props.certKeyName
    })
  }
  return items
})

async function copyPem() {
  if (!props.pem) return
  try {
    await navigator.clipboard.writeText(props.pem)
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
.csr-terminal {
  border: 1px solid var(--p-content-border-color);
  border-radius: 0.75rem;
  overflow: hidden;
  background: #0f172a;
}

.csr-terminal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.04);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.csr-terminal__title {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #e2e8f0;
}

.csr-terminal__body {
  margin: 0;
  padding: 1rem;
  min-height: 14rem;
  max-height: 28rem;
  overflow: auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: #86efac;
  white-space: pre-wrap;
  word-break: break-word;
}

.csr-terminal__hint {
  margin: 0;
  padding: 0 1rem 0.75rem;
  font-size: 0.8125rem;
  color: #94a3b8;
}

.csr-terminal__paths {
  padding: 0.75rem 1rem 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.path-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.path-label {
  font-size: 0.75rem;
  color: #94a3b8;
}

.path-row code {
  font-size: 0.8125rem;
  color: #cbd5e1;
  word-break: break-all;
}
</style>
