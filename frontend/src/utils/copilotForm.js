const LB_MONITOR_OPTIONS = [
  { value: 'tcp-default', label: 'tcp-default' },
  { value: 'http', label: 'http' },
  { value: 'ping', label: 'ping' },
  { value: 'none', label: 'No monitor' }
]

const LB_METHOD_OPTIONS = [
  { value: 'LEASTCONNECTION', label: 'LEASTCONNECTION' },
  { value: 'ROUNDROBIN', label: 'ROUNDROBIN' },
  { value: 'SOURCEIP', label: 'SOURCEIP' }
]

const LB_SERVICE_TYPE_OPTIONS = [
  { value: 'HTTP', label: 'HTTP' },
  { value: 'SSL', label: 'SSL' },
  { value: 'TCP', label: 'TCP' },
  { value: 'UDP', label: 'UDP' },
  { value: 'SSL_BRIDGE', label: 'SSL_BRIDGE (SSL pass-through)' }
]

const LB_SELECT_FIELD_PRESETS = {
  monitor: LB_MONITOR_OPTIONS,
  health_monitor: LB_MONITOR_OPTIONS,
  lb_method: LB_METHOD_OPTIONS,
  load_balancing_method: LB_METHOD_OPTIONS,
  service_type: LB_SERVICE_TYPE_OPTIONS,
  serviceType: LB_SERVICE_TYPE_OPTIONS,
  protocol: LB_SERVICE_TYPE_OPTIONS
}

function normalizeLbFormFields(form) {
  if (!form?.fields?.length) return form
  let changed = false
  const fields = form.fields.map((field) => {
    const preset = LB_SELECT_FIELD_PRESETS[field.id]
    if (preset && (field.type !== 'select' || !field.options?.length)) {
      changed = true
      return { ...field, type: 'select', options: preset }
    }
    return field
  })
  return changed ? { ...form, fields } : form
}

function parseOptionString(value) {
  const trimmed = value.trim()
  if (!trimmed.startsWith('{')) return null
  try {
    const parsed = JSON.parse(trimmed)
    if (!parsed || typeof parsed !== 'object') return null
    const optionValue = parsed.value != null ? String(parsed.value) : String(parsed.label || trimmed)
    const optionLabel = parsed.label != null ? String(parsed.label) : optionValue
    return { label: optionLabel, value: optionValue }
  } catch {
    return null
  }
}

export function normalizeSelectOptions(options) {
  return (options || []).map((opt) => {
    if (typeof opt === 'string') {
      return parseOptionString(opt) || { label: opt, value: opt }
    }
    const value = opt.value != null ? String(opt.value) : String(opt.label || '')
    const label = opt.label != null ? String(opt.label) : value
    return { label, value }
  })
}

function normalizeForm(form) {
  if (!form) return null
  const normalized = {
    ...form,
    fields: (form.fields || []).map((field) => ({
      ...field,
      options: field.type === 'select' ? normalizeSelectOptions(field.options) : field.options
    }))
  }
  return normalizeLbFormFields(normalized)
}

function findBalancedJson(content, start) {
  let depth = 0
  let inString = false
  let escape = false

  for (let index = start; index < content.length; index += 1) {
    const char = content[index]
    if (inString) {
      if (escape) escape = false
      else if (char === '\\') escape = true
      else if (char === '"') inString = false
      continue
    }
    if (char === '"') {
      inString = true
      continue
    }
    if (char === '{') depth += 1
    else if (char === '}') {
      depth -= 1
      if (depth === 0) return [start, index + 1]
    }
  }
  return null
}

function extractInputForm(payload) {
  if (!payload || typeof payload !== 'object') return null
  if (payload.inputForm && typeof payload.inputForm === 'object') return payload.inputForm
  if (Array.isArray(payload.fields)) return payload
  return null
}

function validateForm(rawForm) {
  if (!rawForm?.title || !Array.isArray(rawForm.fields) || !rawForm.fields.length) return null
  return normalizeLbFormFields({
    title: rawForm.title,
    description: rawForm.description || '',
    submitLabel: rawForm.submitLabel || 'Submit',
    fields: rawForm.fields.map((field) => ({
      ...field,
      options: field.type === 'select' ? normalizeSelectOptions(field.options) : field.options
    }))
  })
}

export function parseInputFormFromContent(content) {
  if (!content) return { content: '', inputForm: null }

  const fence = /```(?:json|jpilot-form)?\s*(\{[\s\S]*?\})\s*```/i.exec(content)
  if (fence) {
    try {
      const form = validateForm(extractInputForm(JSON.parse(fence[1])))
      if (form) {
        return {
          content: (content.slice(0, fence.index) + content.slice(fence.index + fence[0].length)).trim(),
          inputForm: form
        }
      }
    } catch {
      // fall through
    }
  }

  let searchFrom = 0
  while (searchFrom < content.length) {
    const markerIndex = content.indexOf('"inputForm"', searchFrom)
    if (markerIndex === -1) break

    const start = content.lastIndexOf('{', markerIndex)
    if (start === -1) {
      searchFrom = markerIndex + 1
      continue
    }

    const bounds = findBalancedJson(content, start)
    if (!bounds) {
      searchFrom = markerIndex + 1
      continue
    }

    try {
      const form = validateForm(extractInputForm(JSON.parse(content.slice(bounds[0], bounds[1]))))
      if (form) {
        return {
          content: (content.slice(0, bounds[0]) + content.slice(bounds[1])).trim(),
          inputForm: form
        }
      }
    } catch {
      // keep searching
    }
    searchFrom = markerIndex + 1
  }

  return { content, inputForm: null }
}

export function resolveAssistantMessage(msg) {
  if (msg.inputForm) {
    return {
      content: msg.content,
      inputForm: normalizeForm(msg.inputForm),
      formSubmitted: msg.formSubmitted
    }
  }
  const parsed = parseInputFormFromContent(msg.content || '')
  return {
    content: parsed.content,
    inputForm: parsed.inputForm,
    formSubmitted: msg.formSubmitted
  }
}
