// App-wide light/dark theme. PrimeVue is configured with darkModeSelector '.app-dark',
// so toggling that class on <html> flips every PrimeVue component. Persisted per user.
const KEY = 'jpilot_theme'
const DARK_CLASS = 'app-dark'

export function getTheme() {
  return localStorage.getItem(KEY) || 'dark'
}

export function applyTheme(theme) {
  document.documentElement.classList.toggle(DARK_CLASS, theme === 'dark')
}

export function setTheme(theme) {
  localStorage.setItem(KEY, theme)
  applyTheme(theme)
  window.dispatchEvent(new CustomEvent('jpilot-theme-change', { detail: theme }))
}

export function applyStoredTheme() {
  applyTheme(getTheme())
}

export function toggleTheme() {
  const next = getTheme() === 'dark' ? 'light' : 'dark'
  setTheme(next)
  return next
}
