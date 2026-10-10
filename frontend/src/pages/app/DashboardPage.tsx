import { Link } from 'react-router-dom'
import DashboardHeader from '../../components/dashboard/DashboardHeader'
import QuickActions from '../../components/dashboard/QuickActions'
import DashboardEmptyState from '../../components/dashboard/DashboardEmptyState'

export default function DashboardPage() {
  return (
    <>
      <DashboardHeader />
      <section className="panel overview-panel" aria-labelledby="overview-heading">
        <div className="panel-heading"><h2 id="overview-heading">Project Overview</h2><span className="subtle-label">Data not connected</span></div>
        <dl className="stat-row">{['Total Projects', 'Documents Uploaded', 'Evaluations Run', 'Best Strategy'].map(label => <div key={label}><dt>{label}</dt><dd aria-label="Not available">—</dd></div>)}</dl>
      </section>
      <QuickActions />
      <div className="dashboard-columns">
        <section className="panel"><div className="panel-heading"><h2>Recent Projects</h2><Link className="text-link" to="/projects">View all</Link></div><DashboardEmptyState kind="projects" /></section>
        <section className="panel"><div className="panel-heading"><h2>Recent Evaluations</h2><Link className="text-link" to="/evaluations">View all</Link></div><DashboardEmptyState kind="evaluations" /></section>
      </div>
    </>
  )
}
