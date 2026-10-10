import { Link } from 'react-router-dom'
import PageHeader from '../../components/shared/PageHeader'
import EvaluationSummary from '../../components/evaluation/EvaluationSummary'
import AdvancedDetails from '../../components/evaluation/AdvancedDetails'

export default function ResultsPage() {
  return (
    <>
      <PageHeader title="Results" description="Understand which configuration to move forward with, and why."
        action={<Link className="button button-secondary" to="/projects">Go to Projects</Link>} />
      <p className="notice result-notice">No evaluation result is connected. The sections below are ready for a real Day 10 summary.</p>
      {/* Future integration supplies presentation props. No fabricated result is used. */}
      <div className="space-y-6"><EvaluationSummary /><AdvancedDetails /></div>
    </>
  )
}
