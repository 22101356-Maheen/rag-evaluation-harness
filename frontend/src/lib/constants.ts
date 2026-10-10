export const navigation = [
  { label: 'Home', href: '/' },
  { label: 'Features', href: '/features' },
  { label: 'How It Works', href: '/how-it-works' },
]

export const steps = [
  { number: '01', title: 'Create a project', description: 'Give your RAG setup a place to start.' },
  { number: '02', title: 'Upload documents', description: 'Bring the knowledge your answers depend on.' },
  { number: '03', title: 'Run evaluation', description: 'Compare retrieval and answer quality together.' },
  { number: '04', title: 'Use the recommendation', description: 'See what works and what to improve next.' },
]

export const capabilities = [
  { number: '01', title: 'Automatic Evaluation Dataset', description: 'Ragify creates reusable test questions from your uploaded corpus.' },
  { number: '02', title: 'Retrieval Comparison', description: 'Compare Semantic, BM25 and Hybrid retrieval.' },
  { number: '03', title: 'Answer Quality Evaluation', description: 'Measure faithfulness, relevance, correctness and hallucination.' },
  { number: '04', title: 'Explainable Recommendations', description: 'See which configuration performed best, why it won and what to improve.' },
]

export const qualityMetrics = ['Faithfulness', 'Correctness', 'Relevance', 'Hallucination']
