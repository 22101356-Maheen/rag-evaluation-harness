import { Link } from 'react-router-dom'
import EmptyState from '../shared/EmptyState'

export default function DashboardEmptyState({ kind }: { kind: 'projects' | 'evaluations' }) {
  return kind === 'projects'
    ? <EmptyState title="No projects to display yet." description="Project data will appear here once the backend is connected." action={<Link className="text-link" to="/projects">Go to Projects →</Link>} />
    : <EmptyState title="No evaluations to display." description="Evaluation history is not available from the backend yet." action={<Link className="text-link" to="/evaluations">About evaluation history →</Link>} />
}
