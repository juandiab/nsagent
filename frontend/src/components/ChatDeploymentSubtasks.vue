<template>
  <div v-if="subtasks?.length" class="deployment-subtasks">
    <div class="deployment-subtasks-title">Deployment progress</div>
    <ul class="deployment-subtasks-list">
      <li
        v-for="task in subtasks"
        :key="task.id"
        class="deployment-subtask"
        :class="`deployment-subtask--${task.status || 'pending'}`"
      >
        <i :class="statusIcon(task.status)" aria-hidden="true" />
        <span>{{ task.label }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
defineProps({
  subtasks: {
    type: Array,
    default: () => []
  }
})

function statusIcon(status) {
  if (status === 'completed') return 'pi pi-check-circle'
  if (status === 'in_progress') return 'pi pi-spin pi-spinner'
  if (status === 'failed') return 'pi pi-times-circle'
  return 'pi pi-circle'
}
</script>

<style scoped>
.deployment-subtasks {
  margin-top: 0.75rem;
  padding: 0.75rem 0.9rem;
  border: 1px solid var(--surface-border);
  border-radius: 0.75rem;
  background: color-mix(in srgb, var(--surface-ground) 88%, transparent);
}

.deployment-subtasks-title {
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--text-color-secondary);
  margin-bottom: 0.5rem;
}

.deployment-subtasks-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.deployment-subtask {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.92rem;
}

.deployment-subtask--completed {
  color: var(--green-500, #22c55e);
}

.deployment-subtask--in_progress {
  color: var(--primary-color);
}

.deployment-subtask--failed {
  color: var(--red-500, #ef4444);
}

.deployment-subtask--pending {
  color: var(--text-color-secondary);
}
</style>
