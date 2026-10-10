import { Link } from 'react-router-dom'
import { ArrowUpRight, FolderPlus, FolderOpen, BookOpen } from 'lucide-react'

export default function QuickActions() {
  return (
    <section className="quick-actions" aria-labelledby="quick-heading">
      <h2 id="quick-heading">Quick Actions</h2>
      <div className="quick-action-list">
        <Link to="/projects?new=1"><FolderPlus size={20} aria-hidden="true" /><span><strong>Create a project</strong><small>Prepare a home for your documents.</small></span><ArrowUpRight size={17} aria-hidden="true" /></Link>
        <Link to="/projects"><FolderOpen size={20} aria-hidden="true" /><span><strong>Open projects</strong><small>Start with your project workspace.</small></span><ArrowUpRight size={17} aria-hidden="true" /></Link>
        <Link to="/how-it-works"><BookOpen size={20} aria-hidden="true" /><span><strong>Explore the workflow</strong><small>Understand each evaluation stage.</small></span><ArrowUpRight size={17} aria-hidden="true" /></Link>
      </div>
    </section>
  )
}
