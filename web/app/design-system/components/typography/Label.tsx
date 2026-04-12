import { forwardRef, type LabelHTMLAttributes } from 'react'
import { cn } from '../../utils/cn'

interface LabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean
  disabled?: boolean
  size?: 'sm' | 'base'
}

export const Label = forwardRef<HTMLLabelElement, LabelProps>(function Label(
  { required, disabled, size = 'base', className, children, ...props },
  ref
) {
  return (
    <label
      ref={ref}
      className={cn(
        'font-medium leading-normal select-none',
        size === 'sm' ? 'text-xs' : 'text-sm',
        disabled
          ? '[color:var(--text-disabled)] cursor-not-allowed'
          : '[color:var(--text-primary)]',
        className
      )}
      {...props}
    >
      {children}
      {required && (
        <span
          aria-hidden="true"
          className="ml-1 [color:var(--state-error)]"
        >
          *
        </span>
      )}
    </label>
  )
})

Label.displayName = 'Label'
