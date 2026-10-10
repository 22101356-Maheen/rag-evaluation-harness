import { Link } from 'react-router-dom'
import PageHeader from '../../components/shared/PageHeader'
import EmptyState from '../../components/shared/EmptyState'

export default function EvaluationsPage() {
  return (
    <>
      <PageHeader title="Evaluations" description="Keep track of the tests behind your RAG configuration decisions." />
      <section className="panel">
        <div className="panel-heading"><h2>Evaluation history</h2><span className="subtle-label">Unavailable</span></div>
        <EmptyState title="Evaluation history is not available yet." description="The backend does not currently expose evaluation history. No past runs are displayed or simulated here."
          action={<Link className="button button-secondary" to="/projects">Explore project controls</Link>} />
      </section>
      <div className="supporting-note"><h2>Where evaluations begin</h2><p>Evaluation controls belong to a project, where your documents and configuration stay together. Once integration is available, start there to evaluate your corpus.</p><Link className="text-link" to="/how-it-works">Understand the evaluation workflow →</Link></div>
    </>
  )
}
