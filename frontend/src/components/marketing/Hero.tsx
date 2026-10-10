import { ArrowDown, ArrowRight, FileText } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Hero() {
  return (
    <section className="hero container" aria-labelledby="hero-heading">
      <div className="hero-copy">
        <p className="eyebrow"><span className="accent-line" />RAG evaluation, without guesswork</p>
        <h1 id="hero-heading">Know what works<br className="desktop-break" /> before you <span>ship.</span></h1>
        <p className="hero-description">Upload your documents, benchmark retrieval strategies, evaluate answer quality, and get an explainable recommendation for your RAG setup.</p>
        <div className="hero-actions">
          <Link className="button button-primary" to="/sign-up">Try Ragify <ArrowRight size={17} aria-hidden="true" /></Link>
          <Link className="button button-secondary" to="/how-it-works">See how it works <ArrowRight size={16} aria-hidden="true" /></Link>
        </div>
        <p className="hero-note">Your corpus. A fair comparison. A clearer decision.</p>
      </div>
      <figure className="workflow-preview hero-workflow">
        <div className="preview-caption"><span className="mono">THE EVALUATION LAYER</span><span className="preview-label">Ragify</span></div>
        <div className="workflow-source"><FileText size={20} strokeWidth={1.5} aria-hidden="true" /><span>Your documents</span><span className="mono source-type">INPUT</span></div>
        <div className="workflow-connector" aria-hidden="true"><ArrowDown size={18} /></div>
        <div className="hero-stage"><span className="mono">01 / RETRIEVAL</span><p>Semantic · BM25 · Hybrid</p></div>
        <div className="workflow-connector" aria-hidden="true"><ArrowDown size={18} /></div>
        <div className="hero-stage"><span className="mono">02 / EVALUATION</span><p>Context quality. Answer quality.</p></div>
        <div className="workflow-connector" aria-hidden="true"><ArrowDown size={18} /></div>
        <div className="hero-stage hero-stage-final"><span className="mono">03 / RECOMMENDATION</span><p>A configuration. A reason. A next step.</p></div>
        <figcaption>A structured path from your knowledge to a decision.</figcaption>
      </figure>
    </section>
  )
}
