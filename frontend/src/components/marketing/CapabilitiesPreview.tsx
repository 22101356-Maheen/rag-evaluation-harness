import { capabilities } from '../../lib/constants'
import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

export default function CapabilitiesPreview() {
  return (
    <section className="section container capabilities-section" id="features" aria-labelledby="capabilities-heading">
      <div className="capabilities-intro">
        <p className="eyebrow">BUILT FOR THE WHOLE PICTURE</p>
        <h2 id="capabilities-heading">Better retrieval.<br />Better answers.<br /><span>A better basis<br />for your decision.</span></h2>
        <p>Evaluate the parts that matter,<br className="desktop-break" /> together.</p>
        <Link className="text-link section-link" to="/features">Explore all capabilities <ArrowRight size={16} aria-hidden="true" /></Link>
      </div>
      <ol className="capability-list">
        {capabilities.map(capability => <li key={capability.number}><span className="mono">{capability.number}</span><div><h3>{capability.title}</h3><p>{capability.description}</p></div></li>)}
      </ol>
    </section>
  )
}
