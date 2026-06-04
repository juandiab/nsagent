<template>
  <span class="appliance-name-label">
    <span class="appliance-name">{{ appliance.name }}</span>
    <span class="appliance-vendor">({{ vendorText }})</span>
    <Tag v-if="showBeta" value="Beta" severity="warn" class="appliance-beta-tag" />
  </span>
</template>

<script setup>
import { computed } from 'vue'
import Tag from 'primevue/tag'
import { vendorLabel } from '../config/applianceVendors'
import { isJpilotBetaAppliance } from '../config/jpilotApplianceAccess'

const props = defineProps({
  appliance: {
    type: Object,
    required: true
  },
  showBeta: {
    type: Boolean,
    default: undefined
  }
})

const vendorText = computed(() => vendorLabel(props.appliance.vendor, props.appliance.productId))

const showBeta = computed(() =>
  props.showBeta !== undefined ? props.showBeta : isJpilotBetaAppliance(props.appliance)
)
</script>

<style scoped>
.appliance-name-label {
  display: inline-flex;
  align-items: baseline;
  gap: 0.35rem;
  min-width: 0;
}

.appliance-name {
  font-weight: 500;
  color: var(--p-text-color);
}

.appliance-vendor {
  font-size: 0.78em;
  font-weight: 400;
  color: var(--p-text-muted-color);
  white-space: nowrap;
}

.appliance-beta-tag {
  flex-shrink: 0;
  font-size: 0.62rem;
  padding: 0.08rem 0.35rem;
  min-height: 1rem;
}
</style>
