<template>
  <div class="config-form">
    <div v-if="form.description" class="config-form-desc">{{ form.description }}</div>
    <div class="config-form-fields">
      <div v-for="field in visibleFields" :key="field.id" class="config-field">
        <div v-if="field.type === 'boolean'" class="config-field-switch">
          <label :for="fieldId(field.id)" class="config-label">{{ field.label }}</label>
          <ToggleSwitch
            :input-id="fieldId(field.id)"
            v-model="values[field.id]"
            :disabled="submitting"
          />
        </div>
        <template v-else>
          <label :for="fieldId(field.id)" class="config-label">
            {{ field.label }}
            <span v-if="field.required" class="config-required">*</span>
          </label>
          <Textarea
            v-if="field.type === 'textarea'"
            :id="fieldId(field.id)"
            v-model="values[field.id]"
            class="w-full"
            rows="3"
            auto-resize
            :placeholder="field.placeholder || ''"
            :disabled="submitting"
          />
          <div v-else-if="field.type === 'choice'" class="config-choice-list">
            <button
              v-for="opt in selectOptions(field)"
              :key="opt.value"
              type="button"
              class="config-choice-btn"
              :class="{ 'config-choice-btn-active': values[field.id] === opt.value }"
              :disabled="submitting"
              @click="values[field.id] = opt.value"
            >
              <span class="config-choice-label">{{ opt.label }}</span>
              <span v-if="opt.description" class="config-choice-desc">{{ opt.description }}</span>
            </button>
            <InputText
              v-if="showChoiceOther(field)"
              :id="fieldId(otherFieldId(field))"
              v-model="values[otherFieldId(field)]"
              class="w-full config-choice-other"
              :placeholder="otherFieldPlaceholder(field)"
              :disabled="submitting"
            />
          </div>
          <Select
            v-else-if="field.type === 'select'"
            :input-id="fieldId(field.id)"
            v-model="values[field.id]"
            :options="selectOptions(field)"
            optionLabel="label"
            optionValue="value"
            class="w-full"
            :disabled="submitting"
          >
            <template #option="{ option }">
              {{ option.label }}
            </template>
          </Select>
          <InputText
            v-else
            :id="fieldId(field.id)"
            v-model="values[field.id]"
            class="w-full"
            :type="field.type === 'number' ? 'text' : 'text'"
            :inputmode="field.type === 'number' ? 'numeric' : 'text'"
            :placeholder="field.placeholder || ''"
            :disabled="submitting"
          />
        </template>
        <small v-if="field.hint" class="config-hint">{{ field.hint }}</small>
      </div>
    </div>
    <Button
      :label="form.submitLabel || 'Submit'"
      icon="pi pi-check"
      size="small"
      class="config-submit"
      :loading="submitting"
      @click="submit"
    />
  </div>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import ToggleSwitch from 'primevue/toggleswitch'
import { normalizeSelectOptions } from '../utils/copilotForm'

const props = defineProps({
  form: {
    type: Object,
    required: true
  },
  submitting: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit'])

const values = reactive({})

const visibleFields = computed(() => {
  const fields = props.form?.fields || []
  const otherIds = new Set(
    fields.filter((f) => f.type === 'choice').map((f) => `${f.id}_other`)
  )
  return fields.filter((f) => !otherIds.has(f.id))
})

function fieldId(id) {
  return `cfg-${id}`
}

function selectOptions(field) {
  return normalizeSelectOptions(field.options)
}

function otherFieldId(choiceField) {
  return `${choiceField.id}_other`
}

function otherFieldDef(choiceField) {
  const id = otherFieldId(choiceField)
  return props.form.fields.find((f) => f.id === id)
}

function showChoiceOther(choiceField) {
  if (values[choiceField.id] !== 'other') return false
  return Boolean(otherFieldDef(choiceField))
}

function otherFieldPlaceholder(choiceField) {
  const other = otherFieldDef(choiceField)
  return other?.placeholder || other?.label || 'Describe your choice'
}

function initValues(form) {
  for (const key of Object.keys(values)) {
    delete values[key]
  }
  for (const field of form?.fields || []) {
    if (field.type === 'boolean') {
      values[field.id] = field.default === true || field.default === 'true'
    } else {
      values[field.id] = field.default != null ? String(field.default) : ''
    }
  }
}

watch(
  () => props.form,
  (form) => initValues(form),
  { immediate: true, deep: true }
)

function submit() {
  for (const field of props.form.fields) {
    if (field.type === 'choice' && field.required && !values[field.id]) {
      return
    }
    if (field.type === 'choice' && values[field.id] === 'other') {
      const otherId = otherFieldId(field)
      const otherVal = values[otherId]
      if (otherVal == null || String(otherVal).trim() === '') {
        return
      }
    }
    if (!field.required) continue
    const value = values[field.id]
    if (field.type === 'boolean' || field.type === 'choice') continue
    if (value == null || String(value).trim() === '') {
      return
    }
  }

  const payload = {}
  for (const field of props.form.fields) {
    payload[field.id] = field.type === 'boolean' ? Boolean(values[field.id]) : values[field.id]
  }
  emit('submit', payload)
}
</script>

<style scoped>
.config-form {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
  margin-top: 0.75rem;
  padding: 1rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: 0.75rem;
  background: color-mix(in srgb, var(--p-primary-50) 35%, var(--p-content-background));
}

.config-form-desc {
  margin: 0;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.config-form-fields {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.config-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.config-field-switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.config-label {
  font-size: 0.8125rem;
  font-weight: 500;
}

.config-required {
  color: var(--p-red-500);
}

.config-hint {
  color: var(--p-text-muted-color);
  font-size: 0.75rem;
}

.config-submit {
  align-self: flex-start;
}

.config-choice-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.config-choice-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.2rem;
  width: 100%;
  padding: 0.65rem 0.85rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: 0.5rem;
  background: var(--p-content-background);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.config-choice-btn:hover:not(:disabled) {
  border-color: var(--p-primary-color);
}

.config-choice-btn-active {
  border-color: var(--p-primary-color);
  background: color-mix(in srgb, var(--p-primary-50) 45%, var(--p-content-background));
}

.config-choice-label {
  font-size: 0.875rem;
  font-weight: 600;
}

.config-choice-desc {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  line-height: 1.35;
}

.config-choice-other {
  margin-top: 0.25rem;
}
</style>
