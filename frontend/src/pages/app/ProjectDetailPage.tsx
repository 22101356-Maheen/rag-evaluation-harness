import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import PageHeader from '../../components/shared/PageHeader'
import EmptyState from '../../components/shared/EmptyState'
import DocumentUpload from '../../components/projects/DocumentUpload'
import EvaluationControls from '../../components/evaluation/EvaluationControls'

export default function ProjectDetailPage() {
  const { projectId } = useParams()
  return (
    <>
      <Link className="text-link back-link" to="/projects"><ArrowLeft size={15} aria-hidden="true" />All projects</Link>
      <PageHeader title="Project workspace" description="Documents, evaluation controls and recommendations for one project." />
      <div className="project-context"><span className="mono">PROJECT ID</span><span className="project-id">{projectId}</span><p>Project details are not connected. This ID has not been verified.</p></div>
      <div className="project-workspace-grid">
        <div className="space-y-6">
          <section className="panel"><div className="panel-heading"><h2>Upload document</h2><span className="subtle-label">.txt only</span></div><DocumentUpload /></section>
          <section className="panel"><div className="panel-heading"><h2>Documents</h2></div><EmptyState title="No documents to display." description="Uploaded files will appear here once document storage is connected." /></section>
        </div>
        <div className="space-y-6">
          <section className="panel"><div className="panel-heading"><h2>Run Evaluation</h2></div><EvaluationControls /></section>
          <section className="panel"><div className="panel-heading"><h2>Latest Result</h2></div><EmptyState title="No result is available." description="A completed evaluation will provide a recommendation and next step." action={<Link className="text-link" to="/results">View the results interface →</Link>} /></section>
        </div>
      </div>
    </>
  )
}
