import type { EvaluationDetailsView } from './types'

export default function AdvancedDetails({ details }: { details?: EvaluationDetailsView }) {
  const metrics = [
    ['MRR', details?.metrics.mrr], ['Recall@K', details?.metrics.recallAtK],
    ['Precision@K', details?.metrics.precisionAtK], ['Hit@K', details?.metrics.hitAtK],
  ]
  return (
    <details className="disclosure advanced-details">
      <summary>Advanced Details<span>Retrieval metrics & query analysis</span></summary>
      <div className="advanced-content">
        <h2>Retrieval metrics</h2>
        <dl className="stat-row">{metrics.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value ?? '—'}</dd></div>)}</dl>
        <h2>Per-query classifications</h2>
        {details?.queries.length ? <ul className="query-classifications">{details.queries.map(query => (
          <li key={query.id}><h3>{query.question}</h3><p>Primary classification: {query.primaryClassification.replaceAll('_', ' ')}</p><p>Labels: {query.labels.map(label => label.replaceAll('_', ' ')).join(', ')}</p><ul>{query.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul></li>
        ))}</ul> : <p className="empty-inline">No evaluated queries are available yet.</p>}
      </div>
    </details>
  )
}
