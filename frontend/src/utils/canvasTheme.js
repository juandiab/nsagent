/** Theme helpers for animated canvas backgrounds. */

export function isDarkTheme() {
  return document.documentElement.classList.contains('app-dark')
}

export function resolveCanvasColors(light, dark) {
  return isDarkTheme() ? dark : light
}

export function onThemeChange(callback) {
  const observer = new MutationObserver(() => callback())
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
  return () => observer.disconnect()
}

export function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}
