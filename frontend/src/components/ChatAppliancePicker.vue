<template>
  <div class="appliance-picker">
    <p class="picker-copy">Select a NetScaler to connect via the Next-Gen API login.</p>
    <div v-if="loading" class="picker-loading">
      <ProgressSpinner style="width: 1.5rem; height: 1.5rem" stroke-width="4" />
      <span>Loading appliances...</span>
    </div>
    <div v-else-if="!appliances.length" class="picker-empty">
      No NetScalers in inventory.
      <RouterLink to="/appliances">Add one →</RouterLink>
    </div>
    <div v-else class="appliance-grid">
      <button
        v-for="item in appliances"
        :key="item.id"
        type="button"
        class="appliance-card"
        :class="{ 'appliance-card-disabled': !item.enabled }"
        :disabled="connecting || !item.enabled"
        @click="$emit('select', item)"
      >
        <div class="appliance-name">{{ item.name }}</div>
        <div class="appliance-meta">
          <Tag :value="item.environment" severity="secondary" />
          <Tag
            :value="item.enabled ? 'Enabled' : 'Disabled'"
            :severity="item.enabled ? 'success' : 'danger'"
          />
        </div>
        <p v-if="item.notes" class="appliance-notes">{{ item.notes }}</p>
      </button>
    </div>
    <div v-if="connecting" class="picker-connecting">
      <ProgressSpinner style="width: 1rem; height: 1rem" stroke-width="4" />
      <span>Running Next-Gen API login...</span>
    </div>
  </div>
</template>

<script setup>
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'

defineProps({
  appliances: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  connecting: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select'])
</script>

<style scoped>
.appliance-picker {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.picker-copy {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.picker-loading,
.picker-connecting,
.picker-empty {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.appliance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr));
  gap: 0.75rem;
}

.appliance-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.875rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: 0.75rem;
  background: var(--p-content-background);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.appliance-card:hover:not(:disabled) {
  border-color: var(--p-primary-300);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.appliance-card-disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.appliance-name {
  font-weight: 600;
  font-size: 0.9375rem;
}

.appliance-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.appliance-notes {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
}
</style>
