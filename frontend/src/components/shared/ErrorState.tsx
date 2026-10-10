import { CircleAlert } from 'lucide-react'

export default function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state-message error-message" role="alert">
      <CircleAlert size={20} aria-hidden="true" />
      <div><h3>Something went wrong</h3><p>{message}</p></div>
      {onRetry && <button className="button button-secondary" onClick={onRetry}>Try again</button>}
    </div>
  )
}
