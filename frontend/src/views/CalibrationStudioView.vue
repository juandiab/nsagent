<template>
  <div class="page">
    <PageHeader
      title="Calibration Studio"
      subtitle="Synced skills and blueprints from Nexxus Stack Calibration Studio — organized by vendor."
    />

    <div class="studio-placeholder content-panel content-panel-padded">
      <div class="studio-placeholder-inner">
        <div class="studio-placeholder-icon" aria-hidden="true">
          <i class="pi pi-sliders-h" />
        </div>
        <h2 class="studio-placeholder-title m-0">Skills catalog coming soon</h2>
        <p class="studio-placeholder-copy m-0">
          This page will list calibration skills synced from Stack Calibration Studio,
          grouped by vendor — NetScaler, F5, Cisco, and more.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import PageHeader from '../components/PageHeader.vue'
</script>

<style scoped>
.page {
  padding: 0 0.5rem 1rem;
  max-width: 56rem;
}

.studio-placeholder {
  margin-top: 0.5rem;
}

.studio-placeholder-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.75rem;
  padding: 2.5rem 1.5rem;
}

.studio-placeholder-icon {
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.75rem;
  background: var(--p-surface-100);
  border: 1px solid var(--p-content-border-color);
  color: var(--p-text-muted-color);
}

.studio-placeholder-icon i {
  font-size: 1.35rem;
}

.studio-placeholder-title {
  font-size: 1.0625rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.studio-placeholder-copy {
  max-width: 28rem;
  font-size: 0.875rem;
  line-height: 1.55;
  color: var(--p-text-muted-color);
}
</style>
