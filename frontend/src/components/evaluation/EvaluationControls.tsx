import { useState } from 'react'
import type { FormEvent } from 'react'
import { Play } from 'lucide-react'

export type EvaluationOptions = {
  caseCount: number
  strategy: 'semantic' | 'bm25' | 'hybrid'
  chunkSize: number
  overlap: number
  topK: number
}

type EvaluationControlsProps = { onRun?: (options: EvaluationOptions) => void }

export default function EvaluationControls({ onRun }: EvaluationControlsProps) {
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const values = new FormData(event.currentTarget)
    const options: EvaluationOptions = {
      caseCount: Number(values.get('caseCount')),
      strategy: values.get('strategy') as EvaluationOptions['strategy'],
      chunkSize: Number(values.get('chunkSize')),
      overlap: Number(values.get('overlap')),
      topK: Number(values.get('topK')),
    }
    setMessage('')
    if (options.overlap >= options.chunkSize) {
      setError('Overlap must be smaller than chunk size.')
      return
    }
    setError('')
    // This callback is the future integration boundary. No request or simulated run.
    if (onRun) onRun(options)
    else setMessage('Evaluation is not connected. No run was started. A real project with ready documents is required.')
  }

  return (
    <form className="evaluation-controls" onSubmit={submit}>
      <div className="evaluation-intro"><div><h3>Evaluate your RAG setup</h3><p>Use your project corpus to compare retrieval and answer quality.</p></div></div>
      <details className="disclosure">
        <summary>Advanced Settings<span>Optional configuration</span></summary>
        <div className="settings-fields">
          <div className="field"><label htmlFor="case-count">Case Count</label><input id="case-count" name="caseCount" type="number" min={1} max={12} defaultValue={8} required /><p>How many test questions to request (1–12).</p></div>
          <div className="field"><label htmlFor="strategy">Strategy</label><select id="strategy" name="strategy" defaultValue="hybrid"><option value="semantic">Semantic</option><option value="bm25">BM25</option><option value="hybrid">Hybrid</option></select><p>The retrieval approach for this configuration.</p></div>
          <div className="field"><label htmlFor="chunk-size">Chunk Size</label><input id="chunk-size" name="chunkSize" type="number" min={40} max={1000} defaultValue={120} required /><p>How much text is placed in each chunk.</p></div>
          <div className="field"><label htmlFor="overlap">Overlap</label><input id="overlap" name="overlap" type="number" min={0} max={300} defaultValue={20} required /><p>How much text neighboring chunks share.</p></div>
          <div className="field"><label htmlFor="top-k">Top K</label><input id="top-k" name="topK" type="number" min={1} max={20} defaultValue={3} required /><p>How many chunks are retrieved.</p></div>
        </div>
      </details>
      {error && <p className="field-error" role="alert">{error}</p>}
      <div className="evaluation-action"><button type="submit" className="button button-primary"><Play size={15} aria-hidden="true" />Run Evaluation</button><span className="small-note">Preview only. No evaluation will be started.</span></div>
      <p className="form-status" role="status">{message}</p>
    </form>
  )
}
