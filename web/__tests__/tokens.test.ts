import { colorPrimitive, radiusPrimitive, spacingPrimitive, shadowPrimitive } from '../app/design-system/tokens'
import { oklchToString, parseOklch, clampToGamut } from '../app/design-system/utils/oklch'
import { apcaContrast, meetsContrastThreshold } from '../app/design-system/utils/contrast'

describe('Primitive color tokens', () => {
  it('primary palette has 11 steps', () => {
    const steps = Object.keys(colorPrimitive.primary)
    expect(steps).toHaveLength(11)
    expect(steps).toContain('50')
    expect(steps).toContain('950')
  })

  it('neutral palette has 11 steps', () => {
    expect(Object.keys(colorPrimitive.neutral)).toHaveLength(11)
  })

  it('all primary colors are valid OKLCH strings', () => {
    Object.values(colorPrimitive.primary).forEach((val) => {
      expect(val).toMatch(/^oklch\(/)
    })
  })

  it('primary-500 is the brand color', () => {
    expect(colorPrimitive.primary['500']).toBe('oklch(0.60 0.10 250)')
  })
})

describe('Radius tokens', () => {
  it('rounded tone: default is 8px', () => {
    expect(radiusPrimitive.default).toBe('8px')
  })

  it('full radius is 9999px', () => {
    expect(radiusPrimitive.full).toBe('9999px')
  })
})

describe('Spacing tokens', () => {
  it('space-4 is 16px (base unit)', () => {
    expect(spacingPrimitive['4']).toBe('16px')
  })

  it('has expected scale', () => {
    expect(spacingPrimitive['1']).toBe('4px')
    expect(spacingPrimitive['2']).toBe('8px')
    expect(spacingPrimitive['8']).toBe('32px')
  })
})

describe('Shadow tokens', () => {
  it('all shadows use oklch for color', () => {
    expect(shadowPrimitive.sm).toContain('oklch(0 0 0')
    expect(shadowPrimitive.md).toContain('oklch(0 0 0')
    expect(shadowPrimitive.lg).toContain('oklch(0 0 0')
  })
})

describe('OKLCH utilities', () => {
  it('oklchToString formats correctly', () => {
    expect(oklchToString(0.6, 0.1, 250)).toBe('oklch(0.6 0.1 250)')
  })

  it('oklchToString includes alpha when provided', () => {
    expect(oklchToString(0.6, 0.1, 250, 0.5)).toBe('oklch(0.6 0.1 250 / 0.5)')
  })

  it('parseOklch extracts components', () => {
    const result = parseOklch('oklch(0.6 0.1 250)')
    expect(result.l).toBeCloseTo(0.6)
    expect(result.c).toBeCloseTo(0.1)
    expect(result.h).toBeCloseTo(250)
  })

  it('clampToGamut keeps chroma within sRGB bounds', () => {
    const result = clampToGamut(0.5, 0.5, 250)
    expect(result.c).toBeLessThanOrEqual(0.35)
    expect(result.l).toBe(0.5)
    expect(result.h).toBe(250)
  })
})

describe('APCA contrast utilities', () => {
  it('high contrast pair passes', () => {
    // Dark text (L=0.18) on light bg (L=0.98) — should be well above Lc 60
    expect(meetsContrastThreshold(0.18, 0.98)).toBe(true)
  })

  it('same lightness returns near-zero contrast', () => {
    const lc = Math.abs(apcaContrast(0.5, 0.5))
    expect(lc).toBeLessThan(5)
  })

  it('apcaContrast returns a number', () => {
    expect(typeof apcaContrast(0.2, 0.9)).toBe('number')
  })
})
