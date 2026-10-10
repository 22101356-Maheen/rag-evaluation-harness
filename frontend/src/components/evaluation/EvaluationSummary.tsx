import type { EvaluationResultView } from './types'

export default function EvaluationSummary({ result }: { result?: EvaluationResultView }) {
  const metrics = [
    ['Faithfulness', result?.metrics.faithfulness],
    ['Correctness', result?.metrics.correctness],
    ['Relevance', result?.metrics.relevance],
    ['Hallucination', result?.metrics.hallucination],
  ]
  const configuration = [
    ['Strategy', result?.configuration.strategy],
    ['Chunk Size', result?.configuration.chunkSize],
    ['Overlap', result?.configuration.chunkOverlap],
    ['Top K', result?.configuration.topK],
  ]
  const explanations = [
    ['Why this was recommended', result?.whyRecommended],
    ['Strengths', result?.strengths],
    ['Weaknesses', result?.weaknesses],
  ] as const

  return (
    <>
      <section className="panel recommendation-panel" aria-labelledby="recommendation-heading">
        <div className="panel-heading"><h2 id="recommendation-heading">Recommendation</h2><span className="subtle-label">{result ? 'Evaluation summary' : 'No result loaded'}</span></div>
        <div className="recommendation-values">
          <div><p>Recommended Strategy</p><strong>{result?.recommendedStrategy ?? 'No recommendation yet'}</strong></div>
          <div><p>Recommendation Score</p><strong>{result?.recommendationScore ?? '—'}</strong></div>
        </div>
        <div className="guardrail-row"><span>Guardrail Status</span><p>{result?.guardrailStatus ?? 'Not evaluated. Quality checks will appear with a real result.'}</p></div>
      </section>
      <section className="panel" aria-labelledby="quality-heading">
        <div className="panel-heading"><h2 id="quality-heading">Answer quality</h2></div>
        <dl className="stat-row">{metrics.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value ?? '—'}</dd></div>)}</dl>
      </section>
      <section className="panel" aria-labelledby="configuration-heading">
        <div className="panel-heading"><h2 id="configuration-heading">Configuration</h2></div>
        <dl className="configuration-list">{configuration.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value ?? '—'}</dd></div>)}</dl>
      </section>
      <div className="result-explanations">
        {explanations.map(([title, items]) => <section key={title}><h2>{title}</h2>{items?.length ? <ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul> : <p>This explanation will be available with an evaluated result.</p>}</section>)}
      </div>
      <section className="next-step-panel"><h2>Next Step</h2><p>{result?.nextStep ?? 'Connect a real evaluation result to see the recommended next step.'}</p></section>
    </>
  )
}
