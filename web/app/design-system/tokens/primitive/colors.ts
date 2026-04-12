// Primitive color tokens — raw OKLCH palette values
// Do NOT use these directly in components. Use semantic tokens instead.

export const colorPrimitive = {
  primary: {
    '50':  'oklch(0.95 0.03 250)',
    '100': 'oklch(0.88 0.05 250)',
    '200': 'oklch(0.80 0.07 250)',
    '300': 'oklch(0.73 0.08 250)',
    '400': 'oklch(0.67 0.09 250)',
    '500': 'oklch(0.60 0.10 250)',
    '600': 'oklch(0.53 0.10 250)',
    '700': 'oklch(0.47 0.09 250)',
    '800': 'oklch(0.42 0.08 250)',
    '900': 'oklch(0.28 0.06 250)',
    '950': 'oklch(0.18 0.05 250)',
  },
  neutral: {
    '50':  'oklch(0.98 0.005 250)',
    '100': 'oklch(0.94 0.008 250)',
    '200': 'oklch(0.88 0.008 250)',
    '300': 'oklch(0.78 0.008 250)',
    '400': 'oklch(0.65 0.008 250)',
    '500': 'oklch(0.52 0.008 250)',
    '600': 'oklch(0.42 0.008 250)',
    '700': 'oklch(0.34 0.008 250)',
    '800': 'oklch(0.26 0.008 250)',
    '900': 'oklch(0.18 0.008 250)',
    '950': 'oklch(0.13 0.005 250)',
  },
  white: 'oklch(1 0 0)',
  black: 'oklch(0 0 0)',
  // State colors
  success: {
    default: 'oklch(0.55 0.18 145)',
    bg:      'oklch(0.94 0.05 145)',
  },
  warning: {
    default: 'oklch(0.65 0.18 75)',
    text:    'oklch(0.45 0.14 75)',
    bg:      'oklch(0.95 0.06 75)',
  },
  error: {
    default: 'oklch(0.55 0.22 25)',
    hover:   'oklch(0.45 0.20 25)',
    bg:      'oklch(0.95 0.06 25)',
  },
  info: {
    default: 'oklch(0.55 0.18 250)',
    bg:      'oklch(0.94 0.04 250)',
  },
} as const
