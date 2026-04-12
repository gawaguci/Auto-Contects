// APCA contrast utilities

/**
 * Calculate APCA Lc contrast between foreground and background.
 * Based on APCA-W3 0.0.98G algorithm.
 * Returns Lc value (positive for light bg, negative for dark bg).
 */
export function apcaContrast(fgLightness: number, bgLightness: number): number {
  const Yfg = fgLightness ** 2.2
  const Ybg = bgLightness ** 2.2

  const normBG = 0.56
  const normTXT = 0.57
  const revBG = 0.65
  const revTXT = 0.62
  const blkThrs = 0.022
  const blkClmp = 1.414
  const scaleBoW = 1.14
  const scaleWoB = 1.14
  const loBoWoffset = 0.027
  const loWoBoffset = 0.027
  const deltaYmin = 0.0005

  const pFg = Math.max(Yfg, blkThrs) ** blkClmp - blkThrs ** blkClmp
  const pBg = Math.max(Ybg, blkThrs) ** blkClmp - blkThrs ** blkClmp

  if (Math.abs(pBg - pFg) < deltaYmin) return 0

  let Lc: number
  if (pBg > pFg) {
    // Normal polarity (light bg, dark text)
    const SAPC = (pBg ** normBG - pFg ** normTXT) * scaleBoW
    Lc = SAPC < loBoWoffset ? 0 : (SAPC - loBoWoffset) * 100
  } else {
    // Reverse polarity (dark bg, light text)
    const SAPC = (pBg ** revBG - pFg ** revTXT) * scaleWoB
    Lc = SAPC > -loWoBoffset ? 0 : (SAPC + loWoBoffset) * 100
  }

  return Math.round(Lc * 10) / 10
}

/**
 * Check if a text/background pair meets APCA thresholds.
 * Uses Lc 60 as working minimum for body text (16px, weight 400).
 */
export function meetsContrastThreshold(
  fgLightness: number,
  bgLightness: number,
  level: 'pass' | 'preferred' = 'pass'
): boolean {
  const lc = Math.abs(apcaContrast(fgLightness, bgLightness))
  const threshold = level === 'preferred' ? 75 : 60
  return lc >= threshold
}

/**
 * Suggest a foreground lightness that meets the minimum APCA contrast
 * against a given background lightness.
 */
export function suggestForegroundL(bgLightness: number, minContrast = 60): number {
  // Try dark text on light bg first
  for (let l = 0.1; l <= 0.5; l += 0.05) {
    if (Math.abs(apcaContrast(l, bgLightness)) >= minContrast) {
      return parseFloat(l.toFixed(2))
    }
  }
  // Try light text on dark bg
  for (let l = 0.9; l >= 0.5; l -= 0.05) {
    if (Math.abs(apcaContrast(l, bgLightness)) >= minContrast) {
      return parseFloat(l.toFixed(2))
    }
  }
  return bgLightness > 0.5 ? 0.15 : 0.90
}
