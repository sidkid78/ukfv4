// Simple UI components that might be missing from shadcn/ui

import * as React from "react"

// Basic Switch component if not available
export interface SwitchProps {
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
  disabled?: boolean
  className?: string
}

export const Switch = React.forwardRef<HTMLButtonElement, SwitchProps>(
  ({ checked = false, onCheckedChange, disabled = false, className = "" }, ref) => {
    return (
      <button
        ref={ref}
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        className={`
          relative inline-flex h-6 w-11 items-center rounded-full transition-colors
          ${checked ? 'bg-blue-600' : 'bg-gray-200'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          ${className}
        `}
        onClick={() => onCheckedChange?.(!checked)}
      >
        <span
          className={`
            inline-block h-4 w-4 transform rounded-full bg-white transition-transform
            ${checked ? 'translate-x-6' : 'translate-x-1'}
          `}
        />
      </button>
    )
  }
)

Switch.displayName = "Switch"

// Basic ScrollArea component if not available
export interface ScrollAreaProps {
  children: React.ReactNode
  className?: string
  ref?: React.RefObject<HTMLDivElement>
}

export const ScrollArea = React.forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ children, className = "" }, ref) => {
    return (
      <div
        ref={ref}
        className={`overflow-auto ${className}`}
        style={{ scrollbarWidth: 'thin' }}
      >
        {children}
      </div>
    )
  }
)

ScrollArea.displayName = "ScrollArea"
