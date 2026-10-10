const questions = [
  'Which retrieval strategy fits your documents?',
  'How should you choose chunk size and overlap?',
  'Are the answers grounded in retrieved context?',
  'Which change is actually worth making next?',
]

export default function WhyRagify() {
  return (
    <section className="section why-section" aria-labelledby="why-heading">
      <div className="container editorial-split">
        <div>
          <p className="eyebrow">WHY RAGIFY</p>
          <h2 id="why-heading">A working pipeline<br />is only the beginning.</h2>
          <p className="section-copy">Building a RAG application is one challenge. Knowing whether it works well is another.</p>
          <p className="section-copy">Ragify is the evaluation layer between “I built a RAG system” and “I know this RAG system works well.”</p>
        </div>
        <div className="problem-list">
          <p className="list-heading">Turn open questions into measured decisions.</p>
          <ul>{questions.map(question => <li key={question}>{question}</li>)}</ul>
          <p className="editorial-footnote">Problem → Evaluation → Decision</p>
        </div>
      </div>
    </section>
  )
}
