import { useSearchParams } from 'react-router-dom'
import { Plus } from 'lucide-react'
import PageHeader from '../../components/shared/PageHeader'
import ProjectList from '../../components/projects/ProjectList'
import ProjectForm from '../../components/projects/ProjectForm'
import Dialog from '../../components/ui/Dialog'

export default function ProjectsPage() {
  const [params, setParams] = useSearchParams()
  const creating = params.get('new') === '1'
  function setCreating(open: boolean) {
    const next = new URLSearchParams(params)
    if (open) next.set('new', '1')
    else next.delete('new')
    setParams(next, { replace: true })
  }

  return (
    <>
      <PageHeader title="Projects" description="Organize documents and evaluations around the systems you are building."
        action={<button className="button button-primary" onClick={() => setCreating(true)}><Plus size={16} aria-hidden="true" />New Project</button>} />
      <section className="panel" aria-labelledby="projects-heading">
        <div className="panel-heading"><h2 id="projects-heading">Your projects</h2><span className="subtle-label">Backend not connected</span></div>
        {/* Supply a real ResourceState here when project loading is connected. */}
        <ProjectList state={{ status: 'empty' }} onNew={() => setCreating(true)} />
      </section>
      <Dialog open={creating} onClose={() => setCreating(false)} title="New project" description="Define your project. Creating and saving it will be available after backend integration.">
        {creating && <ProjectForm onCancel={() => setCreating(false)} />}
      </Dialog>
    </>
  )
}
