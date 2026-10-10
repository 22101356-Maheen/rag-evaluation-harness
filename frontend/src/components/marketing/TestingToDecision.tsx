const stages = [
  { number: '01', title: 'Retrieval', items: ['Semantic', 'BM25', 'Hybrid'], description: 'Benchmark different ways of finding relevant context.' },
  { number: '02', title: 'Answer quality', items: ['Faithfulness', 'Correctness', 'Relevance', 'Hallucination'], description: 'Measure whether generated answers are useful and grounded in the retrieved information.' },
  { number: '03', title: 'Recommendation', items: ['Recommended configuration', 'Why it performed better', 'What to improve next'], description: 'Turn evaluation results into a clear engineering decision.' },
]

export default function TestingToDecision() {
  return (
    <section className="section decision-section" aria-labelledby="decision-heading">
      <div className="container">
        <p className="eyebrow">FROM TESTING TO DECISION</p>
        <div className="section-heading">
          <h2 id="decision-heading">Three retrieval strategies.<br />One clear direction.</h2>
          <p className="decision-copy">Ragify compares how your RAG pipeline retrieves information, evaluates the answers it produces, and explains which configuration is worth moving forward with.</p>
        </div>
        <ol className="decision-stages">
          {stages.map(stage => (
            <li key={stage.number}>
              <p className="stage-label mono">{stage.number} — {stage.title}</p>
              <ul>{stage.items.map(item => <li key={item}>{item}</li>)}</ul>
              <p>{stage.description}</p>
            </li>
          ))}
        </ol>
        <p className="decision-statement">Not just which setup won — <span>why it won.</span></p>
      </div>
    </section>
  )
}
