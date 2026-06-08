<template>
  <div class="beta-sidebar flex flex-column h-full" :class="{ 'beta-sidebar-drawer': variant === 'drawer' }">
    <div v-if="variant !== 'drawer'" class="beta-sidebar-profile">
      <img src="/jpilot-favicon.png" alt="JPilot" class="beta-sidebar-logo" />
      <span class="beta-sidebar-brand">JPilot</span>
      <span class="beta-sidebar-tagline">AI assistant for your appliances</span>
    </div>

    <div class="beta-sidebar-body">
      <div class="beta-sidebar-toolbar">
        <Button
          label="New chat"
          icon="pi pi-plus"
          size="small"
          class="beta-new-chat-btn"
          :disabled="!canAdd"
          @click="$emit('new-chat')"
        />
        <span class="beta-chat-count">{{ conversationCount }} / {{ maxConversations }}</span>
      </div>

      <IconField class="beta-sidebar-search">
        <InputIcon class="pi pi-search" />
        <InputText
          v-model="searchQuery"
          type="text"
          placeholder="Search chats"
          class="w-full"
        />
      </IconField>

      <div class="beta-sidebar-list">
        <BetaChatPaneCard
          v-for="pane in filteredPanes"
          :key="pane.sessionId"
          :pane="pane"
          :active="pane.sessionId === activeSessionId"
          :deletable="conversationCount > 1"
          @select="$emit('select', pane.sessionId)"
          @delete="$emit('delete', pane.sessionId)"
        />
      </div>

      <p v-if="!canAdd" class="beta-sidebar-limit">
        Conversation limit reached. Delete an old chat to start a new one.
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import Button from 'primevue/button'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import InputText from 'primevue/inputtext'
import BetaChatPaneCard from './BetaChatPaneCard.vue'

const props = defineProps({
  panes: { type: Array, default: () => [] },
  activeSessionId: { type: String, required: true },
  canAdd: { type: Boolean, default: true },
  conversationCount: { type: Number, default: 0 },
  maxConversations: { type: Number, default: 12 },
  /** `drawer` — compact list for mobile slide-over. */
  variant: { type: String, default: 'default' }
})

defineEmits(['select', 'new-chat', 'delete'])

const searchQuery = ref('')

const filteredPanes = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return props.panes
  return props.panes.filter(
    (pane) =>
      pane.title.toLowerCase().includes(q) ||
      pane.preview.toLowerCase().includes(q) ||
      pane.role.label.toLowerCase().includes(q)
  )
})
</script>

<style scoped>
.beta-sidebar {
  min-height: 0;
}

.beta-sidebar-profile {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem 1.5rem;
  border-bottom: 1px solid var(--p-content-border-color);
  text-align: center;
}

.beta-sidebar-logo {
  width: 6rem;
  height: 6rem;
  border-radius: 999px;
  box-shadow: 0 10px 28px rgba(2, 6, 23, 0.12);
}

.beta-sidebar-brand {
  margin-top: 1.25rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.beta-sidebar-tagline {
  margin-top: 0.35rem;
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
  line-height: 1.45;
  max-width: 14rem;
}

.beta-sidebar-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.25rem;
  min-height: 0;
  flex: 1;
}

.beta-sidebar-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.beta-new-chat-btn {
  flex: 1;
}

.beta-chat-count {
  flex-shrink: 0;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  font-variant-numeric: tabular-nums;
}

.beta-sidebar-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  overflow-y: auto;
  min-height: 0;
  flex: 1;
}

.beta-sidebar-limit {
  margin: 0;
  font-size: 0.75rem;
  color: var(--p-orange-500);
  line-height: 1.45;
}

@media (max-width: 991px) {
  .beta-sidebar:not(.beta-sidebar-drawer) .beta-sidebar-profile {
    padding: 1.25rem;
  }

  .beta-sidebar:not(.beta-sidebar-drawer) .beta-sidebar-logo {
    width: 4.5rem;
    height: 4.5rem;
  }

  .beta-sidebar:not(.beta-sidebar-drawer) .beta-sidebar-list {
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
    padding-bottom: 0.25rem;
  }

  .beta-sidebar:not(.beta-sidebar-drawer) .beta-sidebar-list :deep(.beta-pane-card) {
    min-width: 16rem;
  }
}

.beta-sidebar-drawer .beta-sidebar-body {
  padding: 0;
  gap: 0.75rem;
  flex: 1;
  min-height: 0;
}

.beta-sidebar-drawer .beta-sidebar-list {
  flex-direction: column;
  overflow-x: hidden;
  overflow-y: auto;
}

.beta-sidebar-drawer .beta-sidebar-list :deep(.beta-pane-card) {
  min-width: 0;
}
</style>
