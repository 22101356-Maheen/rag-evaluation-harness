import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

export default function AuthFormLayout({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return (
    <section className="container auth-page">
      <div className="auth-intro">
        <p className="eyebrow">KNOW BEFORE YOU SHIP</p>
        <h2>Better answers start<br />with better evidence.</h2>
        <p>Bring your documents. Compare your options. Understand what to improve.</p>
        <ol className="auth-benefits"><li>Evaluate on your own knowledge.</li><li>Compare retrieval and answer quality.</li><li>Get an explainable next step.</li></ol>
        <Link className="text-link" to="/dashboard">Explore the UI preview <ArrowRight size={16} aria-hidden="true" /></Link>
        <p className="small-note">Preview access does not sign you in.</p>
      </div>
      <div className="auth-surface">
        <p className="eyebrow">ACCOUNT ACCESS</p>
        <h1>{title}</h1>
        <p className="auth-description">{description}</p>
        <p className="notice">Interface preview. Authentication is not connected yet.</p>
        {children}
      </div>
    </section>
  )
}
