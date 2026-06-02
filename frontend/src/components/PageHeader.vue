<template>
  <div class="page-header flex flex-column md:flex-row md:align-items-center md:justify-content-between py-4 mb-4 gap-4">
    <div>
      <h1 class="page-title m-0">{{ title }}</h1>
      <p v-if="subtitle" class="page-subtitle m-0 mt-1">{{ subtitle }}</p>
    </div>
    <div class="flex align-items-center gap-2 flex-wrap">
      <IconField v-if="searchable">
        <InputIcon class="pi pi-search" />
        <InputText
          :model-value="search"
          placeholder="Search"
          size="small"
          class="search-input"
          @update:model-value="$emit('update:search', $event)"
        />
      </IconField>
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  searchable: { type: Boolean, default: false },
  search: { type: String, default: '' }
})

defineEmits(['update:search'])
</script>

<style scoped>
.page-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--p-text-color);
  letter-spacing: -0.01em;
}

.page-subtitle {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.search-input {
  width: 100%;
  min-width: 12rem;
}

@media (min-width: 768px) {
  .search-input {
    width: 14rem;
  }
}
</style>
