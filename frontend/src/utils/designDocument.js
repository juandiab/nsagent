/** Hidden marker the Architect role should place on the first line of a final deliverable. */
export const JPILOT_DESIGN_MARKER = '<!-- jpilot-design-document -->'

const DESIGN_SECTION_SIGNALS = [
  'design document',
  'executive summary',
  'document purpose',
  'conceptual architecture',
  'overall design',
  'platform design',
  'network design',
  'handoff for operator'
]

/**
 * True when assistant markdown looks like a completed Architect design deliverable.
 * @param {string} content
 */
export function isDesignDocumentMessage(content) {
  if (!content || typeof content !== 'string') return false
  const text = content.trim()
  if (text.length < 500) return false

  if (text.includes(JPILOT_DESIGN_MARKER)) return true

  const lower = text.toLowerCase()
  if (!lower.includes('handoff for operator')) return false

  const signalHits = DESIGN_SECTION_SIGNALS.filter((s) => lower.includes(s)).length
  if (signalHits >= 2) return true
  return signalHits >= 1 && text.length >= 1200
}

/**
 * @param {string} content
 */
export function stripDesignDocumentMarker(content) {
  if (!content) return ''
  return content.replace(JPILOT_DESIGN_MARKER, '').trimStart()
}

/**
 * @param {string} content
 */
export function designDocumentFilename(content) {
  const body = stripDesignDocumentMarker(content)
  const heading = body.match(/^#\s+(.+)$/m)
  const base = heading
    ? heading[1]
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .slice(0, 48)
    : 'jpilot-design'
  const date = new Date().toISOString().slice(0, 10)
  return `${base || 'jpilot-design'}-${date}.md`
}

/**
 * @param {string} content
 * @param {string} [filename]
 */
export function downloadDesignDocument(content, filename) {
  const markdown = stripDesignDocumentMarker(content)
  const name = filename || designDocumentFilename(markdown)
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
