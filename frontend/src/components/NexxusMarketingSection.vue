<template>
  <section class="nexxus-marketing mt-5">
    <div class="blog-panel content-panel-padded">
      <div class="blog-panel-header flex flex-column md:flex-row md:align-items-end md:justify-content-between gap-3 mb-4">
        <div>
          <p class="section-eyebrow m-0">From Nexxus Tech</p>
          <h3 class="panel-heading mt-1">Articles of interest</h3>
          <p class="section-lead m-0 mt-2">
            Infrastructure, security, and automation reading curated by the JPilot team.
          </p>
        </div>
        <a
          :href="NEXXUS_TECH.blogUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="blog-all-link"
        >
          View all articles
          <i class="pi pi-arrow-up-right" />
        </a>
      </div>

      <div v-if="loading" class="blog-loading py-4 flex justify-content-center">
        <ProgressSpinner style="width: 2rem; height: 2rem" />
      </div>

      <Carousel
        v-else
        :value="articles"
        :num-visible="2"
        :num-scroll="1"
        :responsive-options="carouselResponsive"
        :show-indicators="articles.length > 2"
        circular
        class="blog-carousel"
      >
        <template #item="{ data: article }">
          <a
            :href="nexxusBlogArticleUrl(article.slug)"
            target="_blank"
            rel="noopener noreferrer"
            class="blog-card"
          >
            <div
              class="blog-card-accent"
              :style="{ background: article.coverColor || 'var(--p-primary-500)' }"
            />
            <div class="blog-card-body">
              <div class="blog-card-meta">
                <Tag :value="article.category" severity="secondary" />
                <span class="blog-card-date">{{ formatDate(article.date) }}</span>
              </div>
              <h4 class="blog-card-title">{{ article.title }}</h4>
              <p class="blog-card-excerpt">{{ article.excerpt }}</p>
              <span class="blog-card-read">
                {{ article.readTime }} min read
                <i class="pi pi-arrow-right" />
              </span>
            </div>
          </a>
        </template>
      </Carousel>
    </div>

    <footer class="site-footer mt-4">
      <div class="site-footer-inner flex flex-column md:flex-row md:align-items-center md:justify-content-between gap-3">
        <p class="copyright m-0">
          &copy; {{ currentYear }}
          <a :href="NEXXUS_TECH.websiteUrl" target="_blank" rel="noopener noreferrer">{{ NEXXUS_TECH.name }}</a>.
          All rights reserved. JPilot is developed and maintained by Nexxus Tech.
        </p>
        <nav class="footer-links flex flex-wrap gap-3" aria-label="Nexxus Tech links">
          <a :href="NEXXUS_TECH.websiteUrl" target="_blank" rel="noopener noreferrer">Website</a>
          <a :href="NEXXUS_TECH.blogUrl" target="_blank" rel="noopener noreferrer">Blog</a>
          <a :href="NEXXUS_TECH.contactUrl" target="_blank" rel="noopener noreferrer">Contact</a>
        </nav>
      </div>
    </footer>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import Carousel from 'primevue/carousel'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'
import { NEXXUS_TECH, nexxusBlogArticleUrl } from '../config/nexxusTech'
import { fetchNexxusBlogArticles } from '../services/nexxusBlog'

const articles = ref([])
const loading = ref(true)
const currentYear = new Date().getFullYear()

const carouselResponsive = [
  { breakpoint: '960px', numVisible: 2, numScroll: 1 },
  { breakpoint: '640px', numVisible: 1, numScroll: 1 }
]

function formatDate(value) {
  if (!value) return ''
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

onMounted(async () => {
  articles.value = await fetchNexxusBlogArticles()
  loading.value = false
})
</script>

<style scoped>
.blog-panel {
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: var(--content-radius);
  overflow: hidden;
}

.section-eyebrow {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--p-primary-color);
}

.panel-heading {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.section-lead {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  max-width: 40rem;
  line-height: 1.6;
}

.blog-all-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--p-primary-color);
  text-decoration: none;
  white-space: nowrap;
}

.blog-all-link:hover {
  text-decoration: underline;
}

.blog-all-link i {
  font-size: 0.75rem;
}

.blog-carousel :deep(.p-carousel-item) {
  padding: 0 0.5rem;
}

.blog-carousel :deep(.p-carousel-content) {
  align-items: stretch;
}

.blog-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 13.5rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: 0.875rem;
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  background: var(--p-content-background);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.blog-card:hover {
  border-color: var(--p-primary-200);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}

.blog-card-accent {
  height: 4px;
  flex-shrink: 0;
}

.blog-card-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 1.125rem 1.25rem 1.25rem;
  gap: 0.625rem;
}

.blog-card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.blog-card-date {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  white-space: nowrap;
}

.blog-card-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.35;
  color: var(--p-text-color);
}

.blog-card-excerpt {
  margin: 0;
  flex: 1;
  font-size: 0.8125rem;
  line-height: 1.55;
  color: var(--p-text-muted-color);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.blog-card-read {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.25rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--p-primary-color);
}

.blog-card-read i {
  font-size: 0.7rem;
  transition: transform 0.2s ease;
}

.blog-card:hover .blog-card-read i {
  transform: translateX(2px);
}

.site-footer {
  padding: 1.25rem 0 0.5rem;
  border-top: 1px solid var(--p-content-border-color);
}

.copyright {
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
  line-height: 1.5;
  max-width: 42rem;
}

.copyright a,
.footer-links a {
  color: var(--p-primary-color);
  text-decoration: none;
  font-weight: 500;
}

.copyright a:hover,
.footer-links a:hover {
  text-decoration: underline;
}

.footer-links a {
  font-size: 0.8125rem;
}
</style>

<style>
/* Unscoped dark theme — cerulean blue palette */
html.app-dark .nexxus-marketing .blog-panel {
  background: linear-gradient(165deg, #032a3d 0%, #05354d 55%, #064a6b 100%);
  border-color: #0891b2;
}

html.app-dark .nexxus-marketing .section-eyebrow {
  color: #67e8f9;
}

html.app-dark .nexxus-marketing .panel-heading {
  color: #f0f9ff;
}

html.app-dark .nexxus-marketing .section-lead {
  color: #bae6fd;
}

html.app-dark .nexxus-marketing .blog-all-link {
  color: #67e8f9;
}

html.app-dark .nexxus-marketing .blog-card {
  background: linear-gradient(165deg, #065a73 0%, #007ba7 50%, #0891b2 100%);
  border-color: #22d3ee;
}

html.app-dark .nexxus-marketing .blog-card:hover {
  border-color: #67e8f9;
  box-shadow: 0 8px 28px rgba(0, 186, 222, 0.25);
}

html.app-dark .nexxus-marketing .blog-card-title {
  color: #f0f9ff;
}

html.app-dark .nexxus-marketing .blog-card-excerpt,
html.app-dark .nexxus-marketing .blog-card-date {
  color: #a5d8f0;
}

html.app-dark .nexxus-marketing .blog-card-read {
  color: #cffafe;
}

html.app-dark .nexxus-marketing .copyright {
  color: #a5d8f0;
}

html.app-dark .nexxus-marketing .footer-links a,
html.app-dark .nexxus-marketing .copyright a {
  color: #67e8f9;
}

html.app-dark .nexxus-marketing .site-footer {
  border-top-color: #0891b2;
}

html.app-dark .nexxus-marketing .blog-carousel .p-carousel-prev-button,
html.app-dark .nexxus-marketing .blog-carousel .p-carousel-next-button {
  color: #e0f2fe;
}
</style>
