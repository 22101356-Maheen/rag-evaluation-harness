// Presentation models, not an API client. Map real Day 10 data here during integration.
export type EvaluationResultView = {
  recommendedStrategy: string
  recommendationScore: string
  guardrailStatus: string
  configuration: { chunkSize: number; chunkOverlap: number; topK: number; strategy: string }
  metrics: { faithfulness: string; correctness: string; relevance: string; hallucination: string }
  whyRecommended: string[]
  strengths: string[]
  weaknesses: string[]
  nextStep: string
}

export type EvaluationDetailsView = {
  metrics: { mrr: string; recallAtK: string; precisionAtK: string; hitAtK: string }
  queries: { id: string; question: string; primaryClassification: string; labels: string[]; reasons: string[] }[]
}
