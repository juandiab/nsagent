<template>
  <div class="config-form">
    <div v-if="form.description" class="config-form-desc">{{ form.description }}</div>
    <div class="config-form-fields">
      <div v-for="field in form.fields" :key="field.id" class="config-field">
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
import { reactive, watch } from 'vue'
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

function fieldId(id) {
  return `cfg-${id}`
}

function selectOptions(field) {
  return normalizeSelectOptions(field.options)
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
    if (!field.required) continue
    const value = values[field.id]
    if (field.type === 'boolean') continue
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
</style>
