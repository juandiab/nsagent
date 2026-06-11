/** Color palettes for JPilot Beta chat animated backgrounds. */

export const BETA_BACKGROUND_BASES = {
  constellation: 'white',
  waves: 'white',
  drift: 'black',
  orbit: 'black'
}

/** @param {string} backgroundId */
export function getBetaBackgroundBase(backgroundId) {
  return BETA_BACKGROUND_BASES[backgroundId] || 'white'
}

/** High-contrast palettes tuned for solid white or black canvas bases. */
export const BETA_BACKGROUND_PALETTES = {
  constellation: {
    line: '0,58,108',
    dot: '0,82,150',
    lineOpacity: 0.48,
    dotOpacity: 0.92
  },
  waves: {
    line: '0,72,128',
    opacity: 0.42
  },
  drift: {
    dot: '0,214,255',
    opacity: 0.78
  },
  orbit: {
    ring: '0,196,255',
    dot: '120,235,255',
    ringOpacity: 0.62,
    dotOpacity: 0.95
  }
}
