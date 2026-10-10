import { steps } from '../../lib/constants'
import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

export default function HowItWorksPreview() {
  return (
    <section className="section process-section" id="how-it-works" aria-labelledby="process-heading">
      <div className="container">
        <div className="section-heading">
          <div><p className="eyebrow">HOW IT WORKS</p><h2 id="process-heading">A clear path from documents<br />to decisions.</h2></div>
          <p>Bring your knowledge.<br />Let the evaluation do the comparison.</p>
        </div>
        <ol className="process-list">
          {steps.map(step => <li key={step.number}><span className="step-number mono">{step.number}</span><h3>{step.title}</h3><p>{step.description}</p></li>)}
        </ol>
        <Link className="text-link section-link" to="/how-it-works">Explore the full workflow <ArrowRight size={16} aria-hidden="true" /></Link>
      </div>
    </section>
  )
}
