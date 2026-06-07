<template>
  <div v-if="suggestions.length" class="role-suggestions">
    <div class="role-suggestions-header">
      <span class="role-suggestions-sparkle" aria-hidden="true">
        <i class="pi pi-sparkles" />
      </span>
      <div>
        <p class="role-suggestions-title">Suggested picks for JPilot roles</p>
        <p class="role-suggestions-sub">
          Indicative cloud pricing — tap a card to use that model here.
        </p>
      </div>
    </div>

    <div class="role-suggestions-grid">
      <button
        v-for="item in suggestions"
        :key="item.roleId"
        type="button"
        class="role-suggestion-card"
        :class="[
          `role-suggestion-${item.roleId}`,
          {
            'role-suggestion-selected': item.model && item.model === selectedModel,
            'role-suggestion-unavailable': !item.available
          }
        ]"
        :title="item.available ? `Use ${item.model}` : 'No suitable model in your loaded list'"
        @click="onPick(item)"
      >
        <div class="role-suggestion-head">
          <span class="role-suggestion-icon" aria-hidden="true">
            <i :class="item.theme.icon" />
          </span>
          <div class="role-suggestion-meta">
            <span class="role-suggestion-role">{{ item.theme.label }}</span>
            <span class="role-suggestion-tagline">{{ item.theme.tagline }}</span>
          </div>
        </div>

        <span class="role-suggestion-cost">{{ item.cost }}</span>

        <p class="role-suggestion-model">
          <i class="pi pi-star-fill role-suggestion-star" aria-hidden="true" />
          <span class="role-suggestion-model-name">{{ item.modelLabel }}</span>
        </p>
        <p class="role-suggestion-blurb">{{ item.blurb }}</p>

        <span v-if="!item.available" class="role-suggestion-note">
          No match in loaded models
        </span>
        <span v-else-if="!item.isIdeal" class="role-suggestion-note">
          Best match from your list
        </span>
        <span v-else-if="item.model === selectedModel" class="role-suggestion-note role-suggestion-note-active">
          Selected
        </span>
        <span v-else class="role-suggestion-note role-suggestion-note-action">
          Click to select
        </span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { buildRoleSuggestions } from '../config/modelRoleSuggestions'

const props = defineProps({
  providerType: { type: String, required: true },
  availableModels: { type: Array, default: () => [] },
  selectedModel: { type: String, default: '' }
})

const emit = defineEmits(['select-model'])

const suggestions = computed(() =>
  buildRoleSuggestions(props.providerType, props.availableModels)
)

function onPick(item) {
  if (item.model) {
    emit('select-model', item.model)
  }
}
</script>

<style scoped>
.role-suggestions {
  margin-top: 0.35rem;
  padding: 0.85rem;
  border-radius: 14px;
  border: 1px dashed color-mix(in srgb, var(--p-primary-color) 35%, var(--p-content-border-color));
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--p-primary-color) 8%, transparent), transparent 55%),
    var(--app-nested-surface, var(--p-content-background));
}

.role-suggestions-header {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  margin-bottom: 0.75rem;
}

.role-suggestions-sparkle {
  width: 2rem;
  height: 2rem;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #a855f7, #6366f1);
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.role-suggestions-title {
  margin: 0;
  font-size: 0.8125rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.role-suggestions-sub {
  margin: 0.15rem 0 0;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

.role-suggestions-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.65rem;
}

@media (max-width: 900px) {
  .role-suggestions-grid {
    grid-template-columns: 1fr;
  }
}

.role-suggestion-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.4rem;
  min-width: 0;
  padding: 0.7rem 0.75rem 0.6rem;
  border-radius: 12px;
  border: 1px solid transparent;
  text-align: left;
  cursor: pointer;
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    border-color 0.15s ease;
  overflow: hidden;
}

.role-suggestion-card::before {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0;
  background: linear-gradient(120deg, rgba(255, 255, 255, 0.35), transparent 60%);
  transition: opacity 0.15s ease;
  pointer-events: none;
}

.role-suggestion-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
}

.role-suggestion-card:hover::before {
  opacity: 1;
}

.role-suggestion-card:focus-visible {
  outline: 2px solid var(--p-primary-color);
  outline-offset: 2px;
}

.role-suggestion-architect {
  background: linear-gradient(145deg, #f5f3ff 0%, #ede9fe 55%, #ddd6fe 100%);
  border-color: #c4b5fd;
}

.role-suggestion-operator {
  background: linear-gradient(145deg, #ecfdf5 0%, #d1fae5 55%, #a7f3d0 100%);
  border-color: #6ee7b7;
}

.role-suggestion-analyst {
  background: linear-gradient(145deg, #fffbeb 0%, #fef3c7 55%, #fde68a 100%);
  border-color: #fcd34d;
}

html.app-dark .role-suggestion-architect {
  background: linear-gradient(145deg, #1a0b2e 0%, #4c1d95 45%, #2e1065 100%);
  border-color: #7c3aed;
}

html.app-dark .role-suggestion-operator {
  background: linear-gradient(145deg, #052e16 0%, #14532d 45%, #064e3b 100%);
  border-color: #10b981;
}

html.app-dark .role-suggestion-analyst {
  background: linear-gradient(145deg, #1c1917 0%, #78350f 45%, #451a03 100%);
  border-color: #f59e0b;
}

.role-suggestion-selected {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--p-primary-color) 55%, transparent);
}

.role-suggestion-unavailable {
  opacity: 0.82;
  cursor: default;
}

.role-suggestion-unavailable:hover {
  transform: none;
  box-shadow: none;
}

.role-suggestion-head {
  display: flex;
  align-items: flex-start;
  gap: 0.45rem;
  min-width: 0;
}

.role-suggestion-icon {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.55);
  flex-shrink: 0;
}

html.app-dark .role-suggestion-icon {
  background: rgba(0, 0, 0, 0.25);
}

.role-suggestion-architect .role-suggestion-icon {
  color: #6d28d9;
}

.role-suggestion-operator .role-suggestion-icon {
  color: #047857;
}

.role-suggestion-analyst .role-suggestion-icon {
  color: #b45309;
}

html.app-dark .role-suggestion-architect .role-suggestion-icon {
  color: #c4b5fd;
}

html.app-dark .role-suggestion-operator .role-suggestion-icon {
  color: #6ee7b7;
}

html.app-dark .role-suggestion-analyst .role-suggestion-icon {
  color: #fcd34d;
}

.role-suggestion-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}

.role-suggestion-role {
  font-size: 0.8125rem;
  font-weight: 700;
  line-height: 1.2;
}

.role-suggestion-tagline {
  font-size: 0.6875rem;
  color: var(--p-text-muted-color);
  line-height: 1.25;
}

.role-suggestion-cost {
  align-self: flex-start;
  max-width: 100%;
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.35;
  padding: 0.22rem 0.45rem;
  border-radius: 999px;
  white-space: normal;
  overflow-wrap: anywhere;
}

.role-suggestion-architect .role-suggestion-cost {
  background: rgba(124, 58, 237, 0.14);
  color: #6d28d9;
}

.role-suggestion-operator .role-suggestion-cost {
  background: rgba(5, 150, 105, 0.14);
  color: #047857;
}

.role-suggestion-analyst .role-suggestion-cost {
  background: rgba(217, 119, 6, 0.14);
  color: #b45309;
}

html.app-dark .role-suggestion-architect .role-suggestion-cost {
  color: #ddd6fe;
}

html.app-dark .role-suggestion-operator .role-suggestion-cost {
  color: #a7f3d0;
}

html.app-dark .role-suggestion-analyst .role-suggestion-cost {
  color: #fde68a;
}

.role-suggestion-model {
  margin: 0;
  font-size: 0.8125rem;
  font-weight: 600;
  line-height: 1.3;
  display: flex;
  align-items: flex-start;
  gap: 0.3rem;
  min-width: 0;
}

.role-suggestion-model-name {
  min-width: 0;
  overflow-wrap: anywhere;
}

.role-suggestion-star {
  font-size: 0.65rem;
  opacity: 0.85;
  margin-top: 0.15rem;
  flex-shrink: 0;
}

.role-suggestion-architect .role-suggestion-star {
  color: #7c3aed;
}

.role-suggestion-operator .role-suggestion-star {
  color: #059669;
}

.role-suggestion-analyst .role-suggestion-star {
  color: #d97706;
}

.role-suggestion-blurb {
  margin: 0;
  font-size: 0.6875rem;
  line-height: 1.35;
  color: var(--p-text-muted-color);
}

.role-suggestion-note {
  margin-top: 0.1rem;
  font-size: 0.625rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--p-text-muted-color);
}

.role-suggestion-note-active {
  color: var(--p-primary-color);
}

.role-suggestion-note-action {
  opacity: 0;
  transition: opacity 0.15s ease;
}

.role-suggestion-card:not(.role-suggestion-unavailable):hover .role-suggestion-note-action {
  opacity: 1;
}
</style>
