import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import FinalCTA from '../../components/marketing/FinalCTA'

const groups = [
  {
    number: '01', title: 'Evaluation setup', description: 'Start with the knowledge your system actually uses.',
    items: [
      { title: 'Automatic Evaluation Dataset', body: 'Generate questions and evidence-backed reference answers from small sections of your uploaded corpus. Reuse the dataset to compare configurations on the same questions.' },
    ],
  },
  {
    number: '02', title: 'Retrieval evaluation', description: 'Compare how context is found, not just what an answer sounds like.',
    items: [
      { title: 'Retrieval Strategy Comparison', body: 'Evaluate retrieval settings against the same corpus and questions. Compare strategy, chunk size, overlap and the number of retrieved chunks.' },
      { title: 'Semantic Retrieval', body: 'Find context by meaning through embedding similarity. Useful when a question and its answer use different wording.' },
      { title: 'BM25 Retrieval', body: 'Rank passages by keyword relevance. A complementary approach when exact terminology matters.' },
      { title: 'Hybrid Retrieval', body: 'Combine semantic and keyword rankings to bring both signals into retrieval.' },
      { title: 'Retrieval Metrics', body: 'Hit@K checks whether evidence was found. Precision@K measures relevant results, Recall@K measures evidence coverage, and MRR measures how early relevant context appears.' },
    ],
  },
  {
    number: '03', title: 'Answer quality', description: 'Evaluate the answer as well as the context behind it.',
    items: [
      { title: 'Faithfulness', body: 'Measure how well factual answer claims are supported by the retrieved context.' },
      { title: 'Relevance', body: 'Assess how directly the answer addresses the question.' },
      { title: 'Correctness', body: 'Compare the answer with a reference grounded in the source evidence, including how much of the reference it covers.' },
      { title: 'Hallucination Detection', body: 'Flag answer claims that lack support in the retrieved information. These are evaluation signals, not guarantees of truth.' },
    ],
  },
  {
    number: '04', title: 'Failure analysis & recommendation', description: 'Connect the result to your next engineering decision.',
    items: [
      { title: 'Failure Analysis', body: 'Identify missed retrieval, weak faithfulness, unsupported claims, low correctness and low relevance for each question. A question can have more than one failure.' },
      { title: 'Explainable Recommendations', body: 'Use transparent quality guardrails and weighted metrics to compare configurations. See why one was selected, where it remains weak and what to improve next.' },
    ],
  },
]

export default function FeaturesPage() {
  return (
    <>
      <div className="container public-page-intro">
        <p className="eyebrow">RAGIFY CAPABILITIES</p>
        <h1>A complete view of<br />your RAG performance.</h1>
        <p>From the first test question to the next configuration decision. Understand retrieval, answer quality and the relationship between them.</p>
        <Link className="text-link" to="/how-it-works">See how it fits together <ArrowRight size={16} aria-hidden="true" /></Link>
      </div>
      <div className="container feature-groups">
        {groups.map(group => (
          <section className="feature-group" key={group.number} aria-labelledby={`feature-${group.number}`}>
            <div className="feature-group-heading"><span className="mono section-index">{group.number}</span><h2 id={`feature-${group.number}`}>{group.title}</h2><p>{group.description}</p></div>
            <div className="feature-items">{group.items.map(item => <article key={item.title}><h3>{item.title}</h3><p>{item.body}</p></article>)}</div>
          </section>
        ))}
      </div>
      <FinalCTA />
    </>
  )
}
