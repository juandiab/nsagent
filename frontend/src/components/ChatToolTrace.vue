<template>
  <div v-if="tools.length" class="tool-trace-wrap">
    <div
      v-for="(entry, index) in prominentTools"
      :key="`prominent-${index}`"
      class="tool-inline-result"
    >
      <ChatToolResultBody :tool="entry.tool" :view="entry.view" />
    </div>

    <Panel v-if="secondaryTools.length" toggleable collapsed class="tool-trace-panel">
      <template #header>
        <div class="tool-trace-header">
          <i class="pi pi-wrench" />
          <span>Tool activity ({{ secondaryTools.length }})</span>
        </div>
      </template>

      <div class="tool-trace-list">
        <div v-for="(entry, index) in secondaryTools" :key="index" class="tool-trace-item">
          <div class="tool-trace-title">
            <Tag :value="formatToolName(entry.tool.name)" severity="info" />
          </div>
          <ChatToolResultBody :tool="entry.tool" :view="entry.view" />
        </div>
      </div>
    </Panel>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Panel from 'primevue/panel'
import Tag from 'primevue/tag'
import ChatToolResultBody from './ChatToolResultBody.vue'

const PROMINENT_TYPES = new Set([
  'ip-addresses',
  'virtual-ips',
  'applications',
  'vservers',
  'system-info',
  'inventory',
  'service-status'
])

const props = defineProps({
  tools: {
    type: Array,
    default: () => []
  }
})

const enrichedTools = computed(() =>
  props.tools.map((tool) => ({ tool, view: parsed(tool) }))
)

const prominentTools = computed(() => {
  const entries = enrichedTools.value.filter(({ view }) => PROMINENT_TYPES.has(view.type))
  const applicationTables = entries.filter(({ view }) => view.type === 'applications')
  if (applicationTables.length <= 1) {
    return entries
  }
  const preferred = applicationTables.find(({ tool }) => tool.name === 'netscaler_list_virtual_servers')
    || applicationTables[applicationTables.length - 1]
  return [
    ...entries.filter(({ view }) => view.type !== 'applications'),
    preferred
  ]
})

const secondaryTools = computed(() =>
  enrichedTools.value.filter(({ view }) => !PROMINENT_TYPES.has(view.type))
)

function formatToolName(name) {
  return name.replace(/^netscaler_/, '').replace(/_/g, ' ')
}

function unwrapToolData(data) {
  if (data && typeof data === 'object' && data.data && typeof data.data === 'object' && !Array.isArray(data.data)) {
    return data.data
  }
  return data
}

function parsed(tool) {
  try {
    const data = unwrapToolData(JSON.parse(tool.result))

    if (tool.name === 'netscaler_list_inventory' && Array.isArray(data)) {
      return { type: 'inventory', items: data }
    }

    if (tool.name === 'netscaler_test_connection' && typeof data === 'object') {
      return {
        type: 'connection',
        success: Boolean(data.success),
        message: data.message || 'No message returned'
      }
    }

    if (
      (tool.name === 'netscaler_list_applications'
        || tool.name === 'netscaler_list_lb_vservers'
        || tool.name === 'netscaler_list_virtual_servers')
      && (Array.isArray(data) || (typeof data === 'object' && Array.isArray(data.virtualServers)))
    ) {
      const items = Array.isArray(data) ? data : data.virtualServers
      return {
        type: 'applications',
        items: items.map((item) => ({
          name: item.name,
          virtualIp: item.virtualIp || item.virtual_ip || item.ipv46 || '',
          protocol: item.protocol || item.servicetype || '',
          port: item.port || '',
          serverCount: item.serverCount ?? (Array.isArray(item.servers) ? item.servers.length : 0),
          state: item.state || item.curstate || '',
          source: item.source || item.type || ''
        })),
        summary: Array.isArray(data)
          ? undefined
          : {
              virtualServerCount: data.virtualServerCount,
              nextGenCount: data.nextGenCount,
              classicCount: data.classicCount
            }
      }
    }

    if (tool.name === 'netscaler_create_application' && typeof data === 'object') {
      return {
        type: 'create-application',
        success: Boolean(data.success),
        name: data.application?.name || '',
        virtualIp: data.application?.virtual_ip || '',
        port: data.application?.port || '',
        protocol: data.application?.protocol || '',
        servers: data.application?.servers || []
      }
    }

    if (tool.name === 'netscaler_list_virtual_ips' && Array.isArray(data)) {
      return { type: 'virtual-ips', items: data }
    }

    if (tool.name === 'netscaler_list_ip_addresses' && typeof data === 'object' && Array.isArray(data.addresses)) {
      return {
        type: 'ip-addresses',
        items: data.addresses.map((item) => ({
          ipAddress: item.ipAddress || item.ipaddress || '',
          type: item.type || '',
          source: item.source || '',
          name: item.name || '',
          port: item.port || '',
          application: item.application || '',
          state: item.state || ''
        })),
        summary: {
          managementIp: data.managementIp,
          ipCount: data.ipCount
        }
      }
    }

    if (tool.name === 'netscaler_list_service_status' && typeof data === 'object') {
      return {
        type: 'service-status',
        summary: {
          downCount: data.downCount,
          downOnly: data.downOnly
        },
        services: data.services || [],
        serviceGroups: data.serviceGroups || []
      }
    }

    if (tool.name === 'search_netscaler_nextgen_api' && typeof data === 'object') {
      const guide = data.guideMatches || data
      const items = []
      for (const excerpt of guide.memoryExcerpts || data.memoryExcerpts || []) {
        items.push({
          title: `Memory: ${excerpt.title}`,
          url: guide.memorySourceFile || data.memorySourceFile || guide.guideUrl || '',
          description: excerpt.content
        })
      }
      for (const excerpt of guide.excerpts || data.excerpts || []) {
        items.push({
          title: 'Next-Gen API (official)',
          url: guide.guideUrl || data.guideUrl || guide.apiDocsUrl || '',
          description: excerpt
        })
      }
      for (const match of guide.apiReferenceMatches || data.apiReferenceMatches || []) {
        items.push({
          title: `${match.method} ${match.name}`,
          url: guide.apiDocsUrl || data.apiDocsUrl || '',
          description: `${match.category} — ${match.path}`
        })
      }
      for (const path of guide.suggestedGetPaths || data.suggestedGetPaths || []) {
        items.push({
          title: 'Suggested GET path',
          url: guide.apiDocsUrl || '',
          description: path
        })
      }
      return { type: 'web-search', items }
    }

    if (tool.name === 'search_netscaler_cli_reference' && typeof data === 'object') {
      const items = []
      if (data.retrievalMode) {
        items.push({
          title: `Retrieval: ${data.retrievalMode}`,
          url: data.referenceUrl || '',
          description: data.retrievalMode === 'command'
            ? 'Matched specific CLI command(s) — section excerpts omitted.'
            : 'Broader section context included for workflow or ambiguous query.'
        })
      }
      for (const excerpt of data.memoryExcerpts || []) {
        items.push({
          title: `CLI memory: ${excerpt.title}`,
          url: data.memorySourceFile || data.referenceUrl || '',
          description: excerpt.content
        })
      }
      for (const command of data.recommendedCommands || []) {
        items.push({
          title: command.command,
          url: command.docUrl || data.referenceUrl || '',
          description: [
            command.topic,
            command.officialSyntax,
            ...(command.aliases || []).map((alias) => `Alias: ${alias}`),
            ...(command.invalidPatterns || []).map((bad) => `Invalid: ${bad}`)
          ].filter(Boolean).join(' · ')
        })
      }
      for (const excerpt of data.excerpts || []) {
        items.push({ title: 'CLI reference', url: data.referenceUrl || '', description: excerpt })
      }
      return { type: 'web-search', items }
    }

    if (tool.name === 'netscaler_run_cli_commands' && typeof data === 'object' && Array.isArray(data.results)) {
      return {
        type: 'ssh-batch',
        success: data.success !== false,
        items: data.results.map((item) => ({
          command: item.command,
          success: item.success !== false && item.commandFailed !== true,
          output: item.output,
          exitStatus: item.exitStatus
        })),
        summary: {
          commandCount: data.commandCount,
          executedCount: data.executedCount
        }
      }
    }

    if ((tool.name === 'netscaler_ssh_run_command' || tool.name === 'netscaler_run_cli_command') && typeof data === 'object') {
      const success = data.success !== false && data.commandFailed !== true && (data.exitStatus === 0 || data.exitStatus == null)
      return {
        type: 'ssh-result',
        success,
        fields: {
          Command: data.command,
          Host: data.host,
          Port: data.port,
          'Exit status': data.exitStatus,
          Success: success ? 'yes' : 'no',
          'Suggested command': data.suggestedCommand,
          'Retry hint': data.retryHint,
          Output: data.output,
          Stderr: data.stderr
        }
      }
    }

    if (tool.name === 'netscaler_add_ip_address' && typeof data === 'object') {
      return {
        type: 'system-info',
        fields: {
          Success: data.success ? 'yes' : 'no',
          Operation: data.operation,
          'IP address': data.ipAddress,
          Type: data.type,
          Netmask: data.netmask,
          Host: data.host,
          'CLI equivalent': data.classicCliEquivalent,
          'Config saved': data.configSaved,
          Warning: data.saveWarning
        }
      }
    }

    if (tool.name === 'netscaler_get_system_info' && typeof data === 'object') {
      return {
        type: 'system-info',
        fields: {
          Host: data.host,
          'Management IP': data.managementIp || data.ipAddress,
          Hostname: data.hostname,
          'Firmware version': data.firmwareVersion || data.version,
          'Build number': data.buildNumber,
          'Serial number': data.serialNumber,
          Platform: data.platform,
          Mode: data.mode,
          API: data.api,
          'API path': data.apiPath,
          User: data.authenticatedUser,
          Applications: data.applicationCount,
          'Next-Gen available': data.nextGenApiAvailable
        }
      }
    }
  } catch {
    // fall through to raw display
  }

  return { type: 'raw' }
}
</script>

<style scoped>
.tool-trace-wrap {
  margin-top: 0.75rem;
}

.tool-inline-result {
  margin-bottom: 0.75rem;
}

.tool-trace-panel {
  margin-top: 0;
}

.tool-trace-panel :deep(.p-panel-header) {
  padding: 0.5rem 0.75rem;
}

.tool-trace-panel :deep(.p-panel-content) {
  padding: 0.75rem;
}

.tool-trace-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
}

.tool-trace-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.tool-trace-title {
  margin-bottom: 0.5rem;
}

.tool-formatted :deep(.p-datatable) {
  font-size: 0.8125rem;
}

.tool-message {
  margin: 0;
}

.tool-kv {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.35rem 1rem;
  margin: 0;
  font-size: 0.8125rem;
}

.tool-kv dt {
  font-weight: 600;
  color: var(--p-text-muted-color);
}

.tool-kv dd {
  margin: 0;
}

.tool-raw {
  margin: 0;
  font-size: 0.75rem;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--p-text-muted-color);
  max-height: 10rem;
  overflow: auto;
}

.search-result + .search-result {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--p-content-border-color);
}

.search-title {
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--p-primary-color);
  text-decoration: none;
}

.search-title:hover {
  text-decoration: underline;
}

.search-url {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  margin-top: 0.15rem;
}

.search-desc {
  font-size: 0.8125rem;
  margin-top: 0.35rem;
  line-height: 1.5;
}
</style>
