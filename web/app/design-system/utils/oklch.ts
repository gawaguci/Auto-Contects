// OKLCH utility functions

export function oklchToString(l: number, c: number, h: number, alpha?: number): string {
  if (alpha !== undefined && alpha < 1) {
    return `oklch(${l} ${c} ${h} / ${alpha})`
  }
  return `oklch(${l} ${c} ${h})`
}

export function parseOklch(value: string): { l: number; c: number; h: number; alpha?: number } {
  const match = value.match(
    /oklch\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s*\/\s*([\d.]+))?\s*\)/
  )
  if (!match) throw new Error(`Invalid OKLCH value: ${value}`)
  return {
    l: parseFloat(match[1]),
    c: parseFloat(match[2]),
    h: parseFloat(match[3]),
    alpha: match[4] ? parseFloat(match[4]) : undefined,
  }
}

export function generatePalette(
  baseColor: string,
  steps: number[] = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]
): Record<string, string> {
  const { c, h } = parseOklch(baseColor)
  const lMin = 0.15
  const lMax = 0.95
  const palette: Record<string, string> = {}

  steps.forEach((step, i) => {
    const t = i / (steps.length - 1)
    const l = parseFloat((lMax - t * (lMax - lMin)).toFixed(2))
    // Scale chroma slightly toward edges
    const chromaScale = 1 - Math.abs(t - 0.5) * 0.4
    const scaledC = parseFloat((c * chromaScale).toFixed(3))
    palette[step.toString()] = oklchToString(l, scaledC, h)
  })

  return palette
}

/**
 * Clamp chroma to stay within sRGB gamut approximation.
 * Uses a simple heuristic: reduce C until L*C combination is safe.
 */
export function clampToGamut(
  l: number,
  c: number,
  h: number
): { l: number; c: number; h: number } {
  // sRGB gamut approximation: max chroma decreases near L extremes
  const maxC = maxChroma(l)
  return { l, c: Math.min(c, maxC), h }
}

export function maxChroma(l: number): number {
  // Simplified sRGB gamut limit by lightness
  if (l < 0.1 || l > 0.95) return 0.05
  if (l < 0.2 || l > 0.9) return 0.10
  if (l < 0.3 || l > 0.8) return 0.15
  return 0.35
}

/**
 * Convert OKLCH to approximate sRGB hex for native platforms.
 * Uses a simplified conversion — for production use a proper color math library.
 */
export function oklchToHex(l: number, c: number, h: number): string {
  // Convert OKLCH → Oklab → linear sRGB → sRGB
  const hRad = (h * Math.PI) / 180
  const a = c * Math.cos(hRad)
  const b = c * Math.sin(hRad)

  // Oklab → linear sRGB (approximate)
  const lp = l + 0.3963377774 * a + 0.2158037573 * b
  const mp = l - 0.1055613458 * a - 0.0638541728 * b
  const sp = l - 0.0894841775 * a - 1.2914855480 * b

  const rLin = lp ** 3 - 0.0000001 * mp ** 3 + 0.0000001 * sp ** 3
  const gLin = -0.0000001 * lp ** 3 + mp ** 3 + 0.0000001 * sp ** 3
  const bLin = 0.0000001 * lp ** 3 + 0.0000001 * mp ** 3 + sp ** 3

  const toSRGB = (v: number) => {
    const clamped = Math.max(0, Math.min(1, v))
    return clamped <= 0.0031308
      ? Math.round(clamped * 12.92 * 255)
      : Math.round((1.055 * clamped ** (1 / 2.4) - 0.055) * 255)
  }

  const r = toSRGB(rLin)
  const g = toSRGB(gLin)
  const bVal = toSRGB(bLin)

  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${bVal.toString(16).padStart(2, '0')}`
}
