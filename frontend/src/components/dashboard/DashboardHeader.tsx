import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import PageHeader from '../shared/PageHeader'

export default function DashboardHeader() {
  return <PageHeader title="Welcome to Ragify." description="Your documents, evaluations and next decisions, in one place."
    action={<Link className="button button-primary" to="/projects?new=1"><Plus size={16} aria-hidden="true" />New Project</Link>} />
}
