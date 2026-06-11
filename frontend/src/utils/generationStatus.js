export function formatElapsedMs(elapsedMs) {
  const totalSeconds = Math.max(0, Math.floor((elapsedMs || 0) / 1000))
  if (totalSeconds < 60) {
    return `${totalSeconds}s`
  }
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes}m ${seconds}s`
}

export function formatTokensPerSec(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return null
  }
  return `${Number(value).toLocaleString(undefined, { maximumFractionDigits: 1 })} tok/s`
}

export function generationStatusMeta(status) {
  const parts = [formatElapsedMs(status?.elapsedMs)]
  const speed = formatTokensPerSec(status?.tokensPerSec)
  if (speed) {
    parts.push(speed)
  }
  return parts.join(' · ')
}

/** Stats captured after the last model round (persisted on assistant messages). */
export function formatMessageGenerationStats(stats) {
  if (!stats) return null
  const parts = []
  if (stats.durationMs != null && stats.durationMs > 0) {
    parts.push(formatElapsedMs(stats.durationMs))
  }
  const speed = formatTokensPerSec(stats.tokensPerSec)
  if (speed) {
    parts.push(speed)
  }
  return parts.length ? parts.join(' · ') : null
}
