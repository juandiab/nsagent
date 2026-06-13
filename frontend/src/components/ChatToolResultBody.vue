<template>
  <div v-if="view.type === 'inventory'" class="tool-formatted">
    <DataTable :value="view.items" size="small" striped-rows>
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

  <div v-else-if="view.type === 'connection' || view.type === 'ssh-result'" class="tool-formatted">
    <Message
      v-if="view.type === 'connection'"
      :severity="view.success ? 'success' : 'error'"
      :closable="false"
      class="tool-message"
    >
      {{ view.message }}
    </Message>
    <template v-else>
      <Message
        :severity="view.success ? 'success' : 'error'"
        :closable="false"
        class="tool-message mb-2"
      >
        {{ view.success ? 'Command succeeded' : 'Command failed — check syntax and retry' }}
      </Message>
      <dl class="tool-kv">
        <template v-for="(value, key) in view.fields" :key="key">
          <template v-if="value">
            <dt>{{ key }}</dt>
            <dd>{{ value }}</dd>
          </template>
        </template>
      </dl>
    </template>
  </div>

  <div v-else-if="view.type === 'system-info'" class="tool-formatted">
    <dl class="tool-kv">
      <template v-for="(value, key) in view.fields" :key="key">
        <template v-if="value">
          <dt>{{ key }}</dt>
          <dd>{{ value }}</dd>
        </template>
      </template>
    </dl>
  </div>

  <div v-else-if="view.type === 'web-search'" class="tool-formatted">
    <div v-for="(item, itemIndex) in view.items" :key="itemIndex" class="search-result">
      <a :href="item.url" target="_blank" rel="noopener" class="search-title">{{ item.title }}</a>
      <div class="search-url">{{ item.url }}</div>
      <div class="search-desc">{{ item.description }}</div>
    </div>
  </div>

  <div v-else-if="view.type === 'virtual-ips'" class="tool-formatted">
    <DataTable :value="view.items" size="small" striped-rows>
      <Column field="application" header="Application" />
      <Column field="virtualIp" header="Virtual IP" />
      <Column field="protocol" header="Protocol" />
      <Column field="port" header="Port" />
      <Column field="frontend" header="Frontend" />
      <Column field="source" header="Source" />
    </DataTable>
  </div>

  <div v-else-if="view.type === 'ip-addresses'" class="tool-formatted">
    <div v-if="view.summary?.ipCount != null" class="setting-hint mb-2">
      {{ view.summary.ipCount }} address(es)
      <span v-if="view.summary.managementIp"> · management {{ view.summary.managementIp }}</span>
    </div>
    <DataTable :value="view.items" size="small" striped-rows>
      <Column field="ipAddress" header="IP Address" />
      <Column field="type" header="Type" />
      <Column field="name" header="Name" />
      <Column field="port" header="Port" />
      <Column field="application" header="Application" />
      <Column field="source" header="Source" />
      <Column field="state" header="State" />
    </DataTable>
  </div>

  <div v-else-if="view.type === 'service-status'" class="tool-formatted">
    <div v-if="view.summary?.downCount != null" class="setting-hint mb-2">
      {{ view.summary.downCount }} DOWN target(s)
    </div>
    <DataTable
      v-if="view.services?.length"
      :value="view.services"
      size="small"
      striped-rows
      class="mb-2"
    >
      <Column field="name" header="Service" />
      <Column field="ipAddress" header="IP" />
      <Column field="port" header="Port" />
      <Column field="protocol" header="Protocol" />
      <Column field="state" header="State" />
      <Column header="Bound to">
        <template #body="{ data }">
          {{ (data.boundTo || []).join(', ') || '—' }}
        </template>
      </Column>
    </DataTable>
    <div v-for="group in view.serviceGroups || []" :key="group.name" class="mb-2">
      <div class="setting-hint mb-1">
        Service group {{ group.name }}
        <span v-if="group.boundTo?.length"> · bound to {{ group.boundTo.join(', ') }}</span>
      </div>
      <DataTable :value="group.members || []" size="small" striped-rows>
        <Column field="name" header="Member" />
        <Column field="ipAddress" header="IP" />
        <Column field="port" header="Port" />
        <Column field="state" header="State" />
        <Column field="weight" header="Weight" />
      </DataTable>
    </div>
  </div>

  <div v-else-if="view.type === 'applications'" class="tool-formatted">
    <DataTable :value="view.items" size="small" striped-rows>
      <Column field="name" header="Name" />
      <Column field="virtualIp" header="Virtual IP" />
      <Column field="protocol" header="Protocol" />
      <Column field="port" header="Port" />
      <Column field="serverCount" header="Servers" />
      <Column field="state" header="State" />
    </DataTable>
  </div>

  <div v-else-if="view.type === 'vservers'" class="tool-formatted">
    <DataTable :value="view.items" size="small" striped-rows>
      <Column field="name" header="Name" />
      <Column field="ipv46" header="IP" />
      <Column field="servicetype" header="Type" />
      <Column field="curstate" header="State" />
    </DataTable>
  </div>

  <pre v-else class="tool-raw">{{ tool.result }}</pre>
</template>

<script setup>
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Message from 'primevue/message'
import Tag from 'primevue/tag'

defineProps({
  tool: {
    type: Object,
    required: true
  },
  view: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
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
