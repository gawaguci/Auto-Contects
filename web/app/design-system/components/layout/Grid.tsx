import { forwardRef, type HTMLAttributes } from 'react'
import { cn } from '../../utils/cn'

type GridCols = 1 | 2 | 3 | 4 | 6 | 12
type GridGap = '0' | '1' | '2' | '3' | '4' | '5' | '6' | '8'

const colsMap: Record<GridCols, string> = {
  1:  'grid-cols-1',
  2:  'grid-cols-2',
  3:  'grid-cols-3',
  4:  'grid-cols-4',
  6:  'grid-cols-6',
  12: 'grid-cols-12',
}

const gapMap: Record<GridGap, string> = {
  '0': 'gap-0', '1': 'gap-1', '2': 'gap-2', '3': 'gap-3',
  '4': 'gap-4', '5': 'gap-5', '6': 'gap-6', '8': 'gap-8',
}

interface GridProps extends HTMLAttributes<HTMLDivElement> {
  cols?: GridCols
  gap?: GridGap
}

export const Grid = forwardRef<HTMLDivElement, GridProps>(function Grid(
  { cols = 1, gap = '4', className, children, ...props },
  ref
) {
  return (
    <div
      ref={ref}
      className={cn('grid', colsMap[cols], gapMap[gap], className)}
      {...props}
    >
      {children}
    </div>
  )
})

Grid.displayName = 'Grid'
