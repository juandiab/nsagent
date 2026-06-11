<template>
  <div v-if="prompt && !prompt.resolved" class="role-switch-prompt">
    <div class="role-switch-prompt-actions">
      <Button
        :label="`Stay as ${prompt.currentLabel}`"
        icon="pi pi-arrow-left"
        size="small"
        outlined
        severity="secondary"
        :disabled="disabled"
        @click="$emit('stay')"
      />
      <Button
        :label="`Switch to ${prompt.suggestedLabel}`"
        :icon="prompt.suggestedIcon"
        size="small"
        :disabled="disabled"
        @click="$emit('switch')"
      />
    </div>
  </div>
</template>

<script setup>
import Button from 'primevue/button'

defineProps({
  prompt: {
    type: Object,
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['stay', 'switch'])
</script>

<style scoped>
.role-switch-prompt {
  margin-top: 0.75rem;
}

.role-switch-prompt-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
</style>
