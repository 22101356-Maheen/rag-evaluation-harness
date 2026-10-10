import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import FinalCTA from '../../components/marketing/FinalCTA'

const stages = [
  ['Documents', 'Bring your project knowledge as .txt files. Each project keeps the documents for its own evaluation together.', 'YOUR SOURCE MATERIAL'],
  ['Document Processing', 'Extract usable text from the uploaded documents while preserving the connection to the source.', 'PREPARE'],
  ['Chunking', 'Split text into smaller passages. Chunk size controls passage length; overlap keeps neighboring passages connected.', 'PREPARE'],
  ['Embeddings / Indexing', 'Prepare text for retrieval. Semantic search uses embeddings; BM25 uses the words in the passages.', 'PREPARE'],
  ['Semantic / BM25 / Hybrid Retrieval', 'Choose the retrieval configurations to compare. These define how relevant passages will be ranked.', 'CONFIGURE'],
  ['Synthetic Evaluation Dataset', 'Create reusable questions and reference answers from bounded sections of source evidence. Reference answers stay separate from answer generation.', 'BUILD THE TEST SET'],
  ['Retrieve Relevant Context', 'For each test question, find the top-k passages using the selected retrieval configuration.', 'RUN'],
  ['Answer Generation', 'Generate an answer from only the retrieved context. Hidden reference answers and evidence are not automatically supplied to this step.', 'RUN'],
  ['Answer Quality Evaluation', 'Assess faithfulness, relevance, correctness and hallucination using the completed answer, retrieved context and separate evaluation references.', 'EVALUATE'],
  ['Failure Analysis', 'Use the evaluation metrics to identify retrieval misses and answer-quality weaknesses for each question.', 'UNDERSTAND'],
  ['Recommendation', 'Compare configurations using quality guardrails and a transparent score. Explain the choice and identify the next improvement.', 'DECIDE'],
]

export default function HowItWorksPage() {
  return (
    <>
      <div className="container public-page-intro">
        <p className="eyebrow">THE WORKFLOW</p>
        <h1>Your documents in.<br />A clearer direction out.</h1>
        <p>Follow the path from source text to a recommendation. Each stage has a job, and each result stays connected to what was evaluated.</p>
        <Link className="text-link" to="/features">Explore the capabilities <ArrowRight size={16} aria-hidden="true" /></Link>
      </div>
      <section className="container architecture-section" aria-labelledby="architecture-heading">
        <div className="architecture-aside"><p className="eyebrow">INSIDE THE EVALUATION</p><h2 id="architecture-heading">One pipeline.<br />Traceable decisions.</h2><p>Configuration and dataset preparation happen before test questions run through retrieval and generation.</p><p className="architecture-note">Ground truth is used to evaluate an answer. It does not get a shortcut into the answer itself.</p></div>
        <ol className="architecture-stages">
          {stages.map(([title, description, phase], index) => (
            <li key={title}><span className="architecture-number mono">{String(index + 1).padStart(2, '0')}</span><div><p className="stage-phase mono">{phase}</p><h3>{title}</h3><p>{description}</p></div></li>
          ))}
        </ol>
      </section>
      <FinalCTA />
    </>
  )
}
