// Semantic color tokens — purpose-driven aliases
// Components MUST use only these tokens, never primitive tokens directly.

export const colorSemantic = {
  surface: {
    default: 'var(--color-neutral-50)',
    raised:  'var(--color-white)',
    overlay: 'var(--color-neutral-100)',
    inverse: 'var(--color-neutral-900)',
    muted:   'var(--color-neutral-100)',
  },
  text: {
    primary:   'var(--color-neutral-900)',
    secondary: 'var(--color-neutral-500)',
    tertiary:  'var(--color-neutral-400)',
    disabled:  'var(--color-neutral-300)',
    inverse:   'var(--color-white)',
    brand:     'var(--color-primary-600)',
  },
  border: {
    default: 'var(--color-neutral-200)',
    strong:  'var(--color-neutral-300)',
    subtle:  'var(--color-neutral-100)',
    focus:   'var(--color-primary-500)',
    brand:   'var(--color-primary-500)',
  },
  interactive: {
    primary:        'var(--color-primary-600)',
    primaryHover:   'var(--color-primary-700)',
    primaryActive:  'var(--color-primary-800)',
    primaryBg:      'var(--color-primary-50)',
    primaryText:    'var(--color-primary-700)',
  },
  state: {
    success:     'var(--color-success-default)',
    successBg:   'var(--color-success-bg)',
    warning:     'var(--color-warning-default)',
    warningText: 'var(--color-warning-text)',
    warningBg:   'var(--color-warning-bg)',
    error:       'var(--color-error-default)',
    errorHover:  'var(--color-error-hover)',
    errorBg:     'var(--color-error-bg)',
    info:        'var(--color-info-default)',
    infoBg:      'var(--color-info-bg)',
  },
} as const
