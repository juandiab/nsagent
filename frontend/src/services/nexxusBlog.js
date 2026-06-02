import { NEXXUS_BLOG_FALLBACK } from '../config/nexxusTech'

const BLOG_PROXY_PATH = '/nexxus-blog'
export const MAX_BLOG_ARTICLES = 4

function normalizeArticle(article) {
  return {
    slug: article.slug,
    title: article.title,
    excerpt: article.excerpt,
    category: article.category,
    date: article.date,
    readTime: article.read_time ?? article.readTime,
    coverColor: article.cover_color ?? article.coverColor
  }
}

export async function fetchNexxusBlogArticles() {
  try {
    const response = await fetch(BLOG_PROXY_PATH, { credentials: 'same-origin' })
    if (!response.ok) {
      throw new Error(`Blog proxy returned ${response.status}`)
    }
    const data = await response.json()
    if (!Array.isArray(data) || data.length === 0) {
      throw new Error('Blog proxy returned no articles')
    }
    return data.slice(0, MAX_BLOG_ARTICLES).map(normalizeArticle)
  } catch {
    return NEXXUS_BLOG_FALLBACK.slice(0, MAX_BLOG_ARTICLES).map(normalizeArticle)
  }
}
