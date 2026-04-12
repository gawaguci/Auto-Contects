import { type ElementType, type HTMLAttributes, type Ref } from 'react'
import { cn } from '../../utils/cn'

type TextSize = 'xs' | 'sm' | 'base' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl'
type TextWeight = 'light' | 'normal' | 'medium' | 'semibold' | 'bold'
type TextColor = 'primary' | 'secondary' | 'tertiary' | 'disabled' | 'inverse' | 'brand'

const sizeClasses: Record<TextSize, string> = {
  xs:   'text-xs leading-normal',
  sm:   'text-sm leading-relaxed',
  base: 'text-base leading-loose',
  lg:   'text-lg leading-relaxed',
  xl:   'text-xl leading-normal',
  '2xl': 'text-2xl leading-snug',
  '3xl': 'text-3xl leading-tight',
  '4xl': 'text-4xl leading-tight',
}

const weightClasses: Record<TextWeight, string> = {
  light:    'font-light',
  normal:   'font-normal',
  medium:   'font-medium',
  semibold: 'font-semibold',
  bold:     'font-bold',
}

const colorClasses: Record<TextColor, string> = {
  primary:   '[color:var(--text-primary)]',
  secondary: '[color:var(--text-secondary)]',
  tertiary:  '[color:var(--text-tertiary)]',
  disabled:  '[color:var(--text-disabled)]',
  inverse:   '[color:var(--text-inverse)]',
  brand:     '[color:var(--text-brand)]',
}

interface TextProps extends HTMLAttributes<HTMLElement> {
  as?: ElementType
  size?: TextSize
  weight?: TextWeight
  color?: TextColor
  truncate?: boolean
  ref?: Ref<HTMLElement>
}

export function Text({
  as: Component = 'p',
  size = 'base',
  weight = 'normal',
  color = 'primary',
  truncate = false,
  className,
  children,
  ref,
  ...props
}: TextProps) {
  return (
    <Component
      ref={ref}
      className={cn(
        sizeClasses[size],
        weightClasses[weight],
        colorClasses[color],
        truncate && 'truncate',
        className
      )}
      {...props}
    >
      {children}
    </Component>
  )
}

Text.displayName = 'Text'
