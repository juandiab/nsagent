/** Wait for non-zero canvas container size before starting animations. */

export function bindCanvasResize(canvas, callback) {
  const run = () => {
    if (canvas.offsetWidth > 0 && canvas.offsetHeight > 0) {
      callback()
    }
  }

  run()
  const target = canvas.parentElement || canvas
  const observer = new ResizeObserver(run)
  observer.observe(target)
  window.addEventListener('resize', run, { passive: true })

  return () => {
    observer.disconnect()
    window.removeEventListener('resize', run)
  }
}
