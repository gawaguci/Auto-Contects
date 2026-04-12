// Primitive typography tokens

export const typographyPrimitive = {
  fontFamily: {
    sans: 'Inter, system-ui, -apple-system, sans-serif',
    mono: "'JetBrains Mono', ui-monospace, SFMono-Regular, monospace",
  },
  fontSize: {
    xs:   '0.75rem',   // 12px
    sm:   '0.875rem',  // 14px
    base: '1rem',      // 16px
    lg:   '1.125rem',  // 18px
    xl:   '1.25rem',   // 20px
    '2xl': '1.5rem',   // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem',  // 36px
  },
  fontWeight: {
    light:    '300',
    normal:   '400',
    medium:   '500',
    semibold: '600',
    bold:     '700',
  },
  lineHeight: {
    tight:   '1.2',
    snug:    '1.25',
    normal:  '1.4',
    relaxed: '1.5',
    loose:   '1.6',
  },
  letterSpacing: {
    tight:  '-0.02em',
    normal: '0em',
    wide:   '0.025em',
    wider:  '0.05em',
  },
} as const
