export default function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return <div className="state-message" role="status"><span className="loading-indicator" aria-hidden="true" />{label}</div>
}
