import { useEffect, useId, useRef } from 'react'
import type { ReactNode } from 'react'
import { X } from 'lucide-react'

type DialogProps = {
  open: boolean
  onClose: () => void
  title: string
  description?: string
  children: ReactNode
  className?: string
}

export default function Dialog({ open, onClose, title, description, children, className = '' }: DialogProps) {
  const element = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  const descriptionId = useId()

  useEffect(() => {
    if (open) element.current?.showModal()
    else element.current?.close()
  }, [open])

  return (
    <dialog ref={element} className={`dialog ${className}`} onClose={onClose}
      aria-labelledby={titleId} aria-describedby={description ? descriptionId : undefined}>
      <div className="dialog-heading">
        <h2 id={titleId}>{title}</h2>
        <button className="icon-button" onClick={onClose} aria-label="Close dialog" autoFocus><X size={20} aria-hidden="true" /></button>
      </div>
      {description && <p id={descriptionId} className="dialog-description">{description}</p>}
      {children}
    </dialog>
  )
}
