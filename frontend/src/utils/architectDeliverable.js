import {
  JPILOT_DESIGN_MARKER,
  downloadDesignDocument,
  createDesignDocumentAttachment,
  isDesignDocumentMessage,
  stripDesignDocumentMarker,
  designDocumentFilename
} from './designDocument'

/** Hidden marker the Architect role should place on the first line of a change control deliverable. */
export const JPILOT_CHANGE_CONTROL_MARKER = '<!-- jpilot-change-control-document -->'

const CHANGE_CONTROL_SECTION_SIGNALS = [
  'change control record',
  'change record',
  'maintenance window',
  'implementation plan',
  'rollback plan',
  'pre-change checklist',
  'risk assessment',
  'cab'
]

/**
 * @param {string} content
 */
export function isChangeControlDocumentMessage(content) {
  if (!content || typeof content !== 'string') return false
  const text = content.trim()
  if (text.length < 400) return false

  if (text.includes(JPILOT_CHANGE_CONTROL_MARKER)) return true

  const lower = text.toLowerCase()
  const signalHits = CHANGE_CONTROL_SECTION_SIGNALS.filter((s) => lower.includes(s)).length
  return signalHits >= 3 && lower.includes('rollback')
}

/**
 * @param {string} content
 * @returns {'design' | 'change_control' | null}
 */
export function architectDeliverableType(content) {
  if (isChangeControlDocumentMessage(content)) return 'change_control'
  if (isDesignDocumentMessage(content)) return 'design'
  return null
}

/**
 * @param {string} content
 */
export function isArchitectDeliverableMessage(content) {
  return architectDeliverableType(content) !== null
}

/**
 * @param {string} content
 */
export function canSendDeliverableToOperator(content) {
  const type = architectDeliverableType(content)
  if (!type) return false
  if (type === 'design') return true
  return /handoff for operator/i.test(content || '')
}

/**
 * @param {string} content
 */
export function stripArchitectDeliverableMarker(content) {
  if (!content) return ''
  return content
    .replace(JPILOT_DESIGN_MARKER, '')
    .replace(JPILOT_CHANGE_CONTROL_MARKER, '')
    .trimStart()
}

/**
 * @param {string} content
 */
export function architectDeliverableFilename(content) {
  const body = stripArchitectDeliverableMarker(content)
  const heading = body.match(/^#\s+(.+)$/m)
  const type = architectDeliverableType(content)
  const fallback = type === 'change_control' ? 'jpilot-change-control' : 'jpilot-design'
  const base = heading
    ? heading[1]
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .slice(0, 48)
    : fallback
  const date = new Date().toISOString().slice(0, 10)
  return `${base || fallback}-${date}.md`
}

/**
 * @param {string} content
 * @param {string} [filename]
 */
export function createArchitectDeliverableAttachment(content, filename) {
  const markdown = stripArchitectDeliverableMarker(content)
  const name = filename || architectDeliverableFilename(content)
  const bytes = new TextEncoder().encode(markdown).length
  if (bytes > 1024 * 1024) {
    throw new Error('Document exceeds the 1 MB attachment limit')
  }
  return {
    name,
    kind: 'config',
    mimeType: 'text/markdown',
    data: markdown
  }
}

/**
 * @param {string} content
 * @param {string} [filename]
 */
export function downloadArchitectDeliverable(content, filename) {
  if (isDesignDocumentMessage(content) && !isChangeControlDocumentMessage(content)) {
    return downloadDesignDocument(content, filename)
  }
  const markdown = stripArchitectDeliverableMarker(content)
  const name = filename || architectDeliverableFilename(content)
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = name
  anchor.rel = 'noopener'
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
  return name
}

/**
 * @param {string} content
 */
export function architectDeliverableDownloadLabel(content) {
  return architectDeliverableType(content) === 'change_control'
    ? 'Download change control record'
    : 'Download design document'
}

/** @deprecated use createArchitectDeliverableAttachment */
export { createDesignDocumentAttachment, designDocumentFilename }
