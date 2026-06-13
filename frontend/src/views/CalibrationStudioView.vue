<template>
  <div class="page">
    <PageHeader
      title="Calibration Studio"
      subtitle="Skills synced from Stack Calibration Studio — pull updates and review installed calibrations."
    />

    <div class="content-panel content-panel-padded studio-panel">
      <div class="studio-actions flex align-items-center justify-content-between gap-3 flex-wrap mb-3">
        <div>
          <h2 class="m-0 text-lg font-semibold">Installed skills</h2>
          <p class="m-0 mt-1 text-sm text-color-secondary">
            Sync from {{ studioBaseUrl }} to apply SME-authored calibrations locally.
          </p>
        </div>
        <Button
          label="Sync from Studio"
          icon="pi pi-sync"
          :loading="syncing"
          @click="runSync"
        />
      </div>

      <Message v-if="syncMessage" severity="success" class="mb-3" :closable="false">{{ syncMessage }}</Message>
      <Message v-if="syncError" severity="warn" class="mb-3" :closable="false">{{ syncError }}</Message>

      <DataTable :value="skills" :loading="loading" striped-rows data-key="skillId">
        <Column field="label" header="Skill">
          <template #body="{ data }">
            <div class="font-medium">{{ data.label || data.skillId }}</div>
            <code class="skill-id">{{ data.skillId }}</code>
          </template>
        </Column>
        <Column field="version" header="Version" style="width: 7rem" />
        <Column field="vendor" header="Vendor" style="width: 8rem" />
        <Column field="path" header="Cache path">
          <template #body="{ data }">
            <span class="path-cell">{{ data.path }}</span>
          </template>
        </Column>
      </DataTable>

      <p v-if="!loading && !skills.length" class="empty-copy m-0 mt-3">
        No skills installed yet. Start scstudio locally, then click <strong>Sync from Studio</strong>.
      </p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Message from 'primevue/message'
import PageHeader from '../components/PageHeader.vue'
import { CALIBRATION_STUDIO_BASE_URL } from '../config/calibrationStudio.js'
import { listInstalledCalibrations, syncCalibrationsFromStudio } from '../services/calibrationSync.js'

const studioBaseUrl = CALIBRATION_STUDIO_BASE_URL
const skills = ref([])
const loading = ref(false)
const syncing = ref(false)
const syncMessage = ref('')
const syncError = ref('')

async function load() {
  loading.value = true
  syncError.value = ''
  try {
    skills.value = await listInstalledCalibrations()
  } catch (error) {
    syncError.value = error.response?.data?.detail || error.message || 'Could not load installed skills.'
  } finally {
    loading.value = false
  }
}

async function runSync() {
  syncing.value = true
  syncMessage.value = ''
  syncError.value = ''
  try {
    const result = await syncCalibrationsFromStudio()
    syncMessage.value = result.message || 'Calibration sync completed.'
    await load()
  } catch (error) {
    syncError.value = error.response?.data?.detail || error.message || 'Sync failed.'
  } finally {
    syncing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page {
  padding: 0 0.5rem 1rem;
  max-width: 56rem;
}

.studio-panel {
  margin-top: 0.5rem;
}

.skill-id {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

.path-cell {
  font-size: 0.8125rem;
  word-break: break-all;
}

.empty-copy {
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}
</style>
