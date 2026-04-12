import { type ElementType, type HTMLAttributes, type Ref } from 'react'
import { cn } from '../../utils/cn'

interface BoxProps extends HTMLAttributes<HTMLElement> {
  as?: ElementType
  padding?: '0' | '1' | '2' | '3' | '4' | '5' | '6' | '8' | '10' | '12'
  paddingX?: '0' | '1' | '2' | '3' | '4' | '5' | '6' | '8' | '10' | '12'
  paddingY?: '0' | '1' | '2' | '3' | '4' | '5' | '6' | '8' | '10' | '12'
  surface?: 'default' | 'raised' | 'overlay'
  rounded?: 'none' | 'tight' | 'default' | 'loose' | 'full'
  shadow?: 'none' | 'sm' | 'md' | 'lg'
  border?: boolean
  ref?: Ref<HTMLElement>
}

const paddingMap: Record<string, string> = {
  '0': 'p-0', '1': 'p-1', '2': 'p-2', '3': 'p-3',
  '4': 'p-4', '5': 'p-5', '6': 'p-6', '8': 'p-8',
  '10': 'p-10', '12': 'p-12',
}
const paddingXMap: Record<string, string> = {
  '0': 'px-0', '1': 'px-1', '2': 'px-2', '3': 'px-3',
  '4': 'px-4', '5': 'px-5', '6': 'px-6', '8': 'px-8',
  '10': 'px-10', '12': 'px-12',
}
const paddingYMap: Record<string, string> = {
  '0': 'py-0', '1': 'py-1', '2': 'py-2', '3': 'py-3',
  '4': 'py-4', '5': 'py-5', '6': 'py-6', '8': 'py-8',
  '10': 'py-10', '12': 'py-12',
}

const surfaceMap = {
  default: '[background:var(--surface-default)]',
  raised:  '[background:var(--surface-raised)]',
  overlay: '[background:var(--surface-overlay)]',
}

const roundedMap = {
  none:    'rounded-none',
  tight:   'rounded-tight',
  default: 'rounded-default',
  loose:   'rounded-loose',
  full:    'rounded-full',
}

const shadowMap = {
  none: '',
  sm:   '[box-shadow:var(--shadow-sm)]',
  md:   '[box-shadow:var(--shadow-md)]',
  lg:   '[box-shadow:var(--shadow-lg)]',
}

export function Box({
  as: Component = 'div',
  padding,
  paddingX,
  paddingY,
  surface,
  rounded,
  shadow,
  border = false,
  className,
  children,
  ref,
  ...props
}: BoxProps) {
  return (
    <Component
      ref={ref}
      className={cn(
        padding && paddingMap[padding],
        paddingX && paddingXMap[paddingX],
        paddingY && paddingYMap[paddingY],
        surface && surfaceMap[surface],
        rounded && roundedMap[rounded],
        shadow && shadowMap[shadow],
        border && 'border [border-color:var(--border-default)]',
        className
      )}
      {...props}
    >
      {children}
    </Component>
  )
}

Box.displayName = 'Box'
