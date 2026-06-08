<template>
  <div class="chat-markdown" :class="{ 'chat-markdown-compact': compact }" v-html="rendered" />
</template>

<script setup>
import { computed } from 'vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'

const props = defineProps({
  content: {
    type: String,
    default: ''
  },
  compact: {
    type: Boolean,
    default: false
  }
})

marked.setOptions({
  breaks: true,
  gfm: true
})

const rendered = computed(() => {
  if (!props.content) return ''
  return DOMPurify.sanitize(marked.parse(props.content))
})
</script>

<style scoped>
.chat-markdown {
  line-height: 1.6;
  font-size: 0.9375rem;
}

.chat-markdown :deep(p) {
  margin: 0 0 0.75rem;
}

.chat-markdown :deep(p:last-child) {
  margin-bottom: 0;
}

.chat-markdown :deep(h1),
.chat-markdown :deep(h2),
.chat-markdown :deep(h3),
.chat-markdown :deep(h4) {
  margin: 1rem 0 0.5rem;
  line-height: 1.3;
  font-weight: 600;
}

.chat-markdown :deep(h1:first-child),
.chat-markdown :deep(h2:first-child),
.chat-markdown :deep(h3:first-child) {
  margin-top: 0;
}

.chat-markdown :deep(ul),
.chat-markdown :deep(ol) {
  margin: 0.5rem 0 0.75rem;
  padding-left: 1.25rem;
}

.chat-markdown :deep(li) {
  margin-bottom: 0.35rem;
}

.chat-markdown :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.75rem 0;
  font-size: 0.875rem;
}

.chat-markdown :deep(th),
.chat-markdown :deep(td) {
  border: 1px solid var(--p-content-border-color);
  padding: 0.45rem 0.65rem;
  text-align: left;
}

.chat-markdown :deep(th) {
  background: var(--p-content-background);
  font-weight: 600;
}

.chat-markdown :deep(tr:nth-child(even) td) {
  background: color-mix(in srgb, var(--p-surface-100) 50%, transparent);
}

.chat-markdown :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85em;
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: 0.25rem;
  padding: 0.1rem 0.35rem;
}

.chat-markdown :deep(pre) {
  margin: 0.75rem 0;
  padding: 0.75rem;
  border-radius: 0.5rem;
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  overflow-x: auto;
}

.chat-markdown :deep(pre code) {
  border: none;
  padding: 0;
  background: transparent;
}

.chat-markdown :deep(blockquote) {
  margin: 0.75rem 0;
  padding-left: 0.75rem;
  border-left: 3px solid var(--p-primary-color);
  color: var(--p-text-muted-color);
}

.chat-markdown :deep(hr) {
  border: none;
  border-top: 1px solid var(--p-content-border-color);
  margin: 1rem 0;
}

.chat-markdown :deep(strong) {
  font-weight: 600;
}

.chat-markdown-compact {
  line-height: 1.45;
  font-size: 0.875rem;
}

.chat-markdown-compact :deep(p) {
  margin: 0 0 0.35rem;
}

.chat-markdown-compact :deep(h1),
.chat-markdown-compact :deep(h2),
.chat-markdown-compact :deep(h3),
.chat-markdown-compact :deep(h4) {
  margin: 0.5rem 0 0.25rem;
}

.chat-markdown-compact :deep(ul),
.chat-markdown-compact :deep(ol) {
  margin: 0.25rem 0 0.4rem;
  padding-left: 1.1rem;
}

.chat-markdown-compact :deep(li) {
  margin-bottom: 0.15rem;
}

.chat-markdown-compact :deep(li:last-child) {
  margin-bottom: 0;
}

.chat-markdown-compact :deep(table) {
  margin: 0.4rem 0;
}

.chat-markdown-compact :deep(pre) {
  margin: 0.4rem 0;
  padding: 0.5rem 0.625rem;
}

.chat-markdown-compact :deep(blockquote) {
  margin: 0.4rem 0;
}

.chat-markdown-compact :deep(hr) {
  margin: 0.5rem 0;
}
</style>
