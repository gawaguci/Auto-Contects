import { forwardRef, type HTMLAttributes } from 'react'
import { cn } from '../../utils/cn'

type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6
type HeadingSize = '4xl' | '3xl' | '2xl' | 'xl' | 'lg' | 'base'

const levelDefaults: Record<HeadingLevel, HeadingSize> = {
  1: '4xl',
  2: '3xl',
  3: '2xl',
  4: 'xl',
  5: 'lg',
  6: 'base',
}

const sizeClasses: Record<HeadingSize, string> = {
  '4xl': 'text-4xl font-bold leading-tight tracking-tight',
  '3xl': 'text-3xl font-bold leading-tight tracking-tight',
  '2xl': 'text-2xl font-semibold leading-snug',
  xl:    'text-xl font-semibold leading-snug',
  lg:    'text-lg font-medium leading-normal',
  base:  'text-base font-medium leading-normal',
}

interface HeadingProps extends HTMLAttributes<HTMLHeadingElement> {
  level?: HeadingLevel
  size?: HeadingSize
}

export const Heading = forwardRef<HTMLHeadingElement, HeadingProps>(function Heading(
  { level = 2, size, className, children, ...props },
  ref
) {
  const Tag = `h${level}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
  const resolvedSize = size ?? levelDefaults[level]

  return (
    <Tag
      ref={ref}
      className={cn(
        '[color:var(--text-primary)]',
        sizeClasses[resolvedSize],
        className
      )}
      {...props}
    >
      {children}
    </Tag>
  )
})

Heading.displayName = 'Heading'
