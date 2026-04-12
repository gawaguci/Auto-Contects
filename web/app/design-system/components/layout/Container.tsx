import { forwardRef, type HTMLAttributes } from 'react'
import { cn } from '../../utils/cn'

type ContainerSize = 'sm' | 'md' | 'lg' | 'xl' | 'full'

const sizeMap: Record<ContainerSize, string> = {
  sm:   'max-w-[640px]',
  md:   'max-w-[768px]',
  lg:   'max-w-[1024px]',
  xl:   'max-w-[1280px]',
  full: 'max-w-full',
}

interface ContainerProps extends HTMLAttributes<HTMLDivElement> {
  size?: ContainerSize
  center?: boolean
}

export const Container = forwardRef<HTMLDivElement, ContainerProps>(function Container(
  { size = 'xl', center = true, className, children, ...props },
  ref
) {
  return (
    <div
      ref={ref}
      className={cn(
        'w-full px-4 md:px-6',
        sizeMap[size],
        center && 'mx-auto',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
})

Container.displayName = 'Container'
