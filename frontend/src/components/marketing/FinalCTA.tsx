import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function FinalCTA() {
  return (
    <section className="final-cta" aria-labelledby="cta-heading">
      <div className="container final-cta-inner">
        <div><p className="eyebrow">BUILD WITH A CLEARER PICTURE</p><h2 id="cta-heading">Stop guessing which<br />RAG setup works.</h2></div>
        <Link className="button button-light" to="/sign-up">Try Ragify <ArrowRight size={18} aria-hidden="true" /></Link>
      </div>
    </section>
  )
}
