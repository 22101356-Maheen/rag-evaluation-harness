const audiences = [
  { title: 'AI Engineers', description: 'Compare retrieval approaches and trace weak answers back to their likely cause.' },
  { title: 'Developers building RAG applications', description: 'Test chunking choices and retrieval settings before building further on top of them.' },
  { title: 'Teams testing knowledge assistants', description: 'Evaluate answers against your own documents and agree on what needs improvement.' },
  { title: 'Students & researchers', description: 'Explore retrieval systems with a reusable dataset and a clear basis for comparison.' },
]

export default function WhoItsFor() {
  return (
    <section className="section container audience-section" aria-labelledby="audience-heading">
      <div className="section-heading"><div><p className="eyebrow">WHO IT’S FOR</p><h2 id="audience-heading">For the people building<br />answers people rely on.</h2></div></div>
      <div className="audience-list">
        {audiences.map(audience => <article key={audience.title}><h3>{audience.title}</h3><p>{audience.description}</p></article>)}
      </div>
    </section>
  )
}
