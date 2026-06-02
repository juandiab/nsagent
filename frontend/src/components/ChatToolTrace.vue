<template>
  <Panel toggleable collapsed class="tool-trace-panel">
    <template #header>
      <div class="tool-trace-header">
        <i class="pi pi-wrench" />
        <span>Tool activity ({{ tools.length }})</span>
      </div>
    </template>

    <div class="tool-trace-list">
      <div v-for="(tool, index) in tools" :key="index" class="tool-trace-item">
        <div class="tool-trace-title">
          <Tag :value="formatToolName(tool.name)" severity="info" />
        </div>

        <div v-if="parsed(tool).type === 'inventory'" class="tool-formatted">
          <DataTable :value="parsed(tool).items" size="small" striped-rows>
            <Column field="name" header="Name" />
            <Column field="environment" header="Environment" />
            <Column header="Enabled">
              <template #body="{ data }">
                <Tag
                  :value="data.enabled ? 'Yes' : 'No'"
                  :severity="data.enabled ? 'success' : 'secondary'"
                />
              </template>
            </Column>
          </DataTable>
        </div>

        <div v-else-if="parsed(tool).type === 'connection' || parsed(tool).type === 'ssh-result'" class="tool-formatted">
          <Message
            v-if="parsed(tool).type === 'connection'"
            :severity="parsed(tool).success ? 'success' : 'error'"
            :closable="false"
            class="tool-message"
          >
            {{ parsed(tool).message }}
          </Message>
          <template v-else>
            <Message
              :severity="parsed(tool).success ? 'success' : 'error'"
              :closable="false"
              class="tool-message mb-2"
            >
              {{ parsed(tool).success ? 'Command succeeded' : 'Command failed — check syntax and retry' }}
            </Message>
            <dl class="tool-kv">
              <template v-for="(value, key) in parsed(tool).fields" :key="key">
                <template v-if="value">
                  <dt>{{ key }}</dt>
                  <dd>{{ value }}</dd>
                </template>
              </template>
            </dl>
          </template>
        </div>

        <div v-else-if="parsed(tool).type === 'system-info'" class="tool-formatted">
          <dl class="tool-kv">
            <template v-for="(value, key) in parsed(tool).fields" :key="key">
              <template v-if="value">
                <dt>{{ key }}</dt>
                <dd>{{ value }}</dd>
              </template>
            </template>
          </dl>
        </div>

        <div v-else-if="parsed(tool).type === 'web-search'" class="tool-formatted">
          <div v-for="(item, index) in parsed(tool).items" :key="index" class="search-result">
            <a :href="item.url" target="_blank" rel="noopener" class="search-title">{{ item.title }}</a>
            <div class="search-url">{{ item.url }}</div>
            <div class="search-desc">{{ item.description }}</div>
          </div>
        </div>

        <div v-else-if="parsed(tool).type === 'virtual-ips'" class="tool-formatted">
          <DataTable :value="parsed(tool).items" size="small" striped-rows>
            <Column field="application" header="Application" />
            <Column field="virtualIp" header="Virtual IP" />
            <Column field="protocol" header="Protocol" />
            <Column field="port" header="Port" />
            <Column field="frontend" header="Frontend" />
            <Column field="source" header="Source" />
          </DataTable>
        </div>

        <div v-else-if="parsed(tool).type === 'ip-addresses'" class="tool-formatted">
          <div v-if="parsed(tool).summary?.ipCount != null" class="setting-hint mb-2">
            {{ parsed(tool).summary.ipCount }} address(es)
            <span v-if="parsed(tool).summary.managementIp"> · management {{ parsed(tool).summary.managementIp }}</span>
          </div>
          <DataTable :value="parsed(tool).items" size="small" striped-rows>
            <Column field="ipAddress" header="IP Address" />
            <Column field="type" header="Type" />
            <Column field="name" header="Name" />
            <Column field="port" header="Port" />
            <Column field="application" header="Application" />
            <Column field="source" header="Source" />
            <Column field="state" header="State" />
          </DataTable>
        </div>

        <div v-else-if="parsed(tool).type === 'applications'" class="tool-formatted">
          <DataTable :value="parsed(tool).items" size="small" striped-rows>
            <Column field="name" header="Name" />
            <Column field="virtualIp" header="Virtual IP" />
            <Column field="protocol" header="Protocol" />
            <Column field="port" header="Port" />
            <Column field="serverCount" header="Servers" />
            <Column field="state" header="State" />
          </DataTable>
        </div>

        <div v-else-if="parsed(tool).type === 'vservers'" class="tool-formatted">
          <DataTable :value="parsed(tool).items" size="small" striped-rows>
            <Column field="name" header="Name" />
            <Column field="ipv46" header="IP" />
            <Column field="servicetype" header="Type" />
            <Column field="curstate" header="State" />
          </DataTable>
        </div>

        <pre v-else class="tool-raw">{{ tool.result }}</pre>
      </div>
    </div>
  </Panel>
</template>

<script setup>
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Message from 'primevue/message'
import Panel from 'primevue/panel'
import Tag from 'primevue/tag'

defineProps({
  tools: {
    type: Array,
    default: () => []
  }
})

function formatToolName(name) {
  return name.replace(/^netscaler_/, '').replace(/_/g, ' ')
}

function parsed(tool) {
  try {
    const data = JSON.parse(tool.result)

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
.tool-trace-panel {
  margin-top: 0.75rem;
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
