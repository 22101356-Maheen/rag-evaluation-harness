import type { ReactNode } from 'react'
import { FolderOpen } from 'lucide-react'

type EmptyStateProps = { title: string; description: string; action?: ReactNode }
export default function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <FolderOpen size={25} strokeWidth={1.4} aria-hidden="true" />
      <h3>{title}</h3>
      <p>{description}</p>
      {action && <div className="empty-action">{action}</div>}
    </div>
  )
}
