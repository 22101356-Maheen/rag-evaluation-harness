from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.schemas.experiment import ExperimentConfig


class EvaluationRequest(BaseModel):
    question: str
    retriever: str
    top_k: int


ShortText = Annotated[str, Field(min_length=1, max_length=2000)]


class StructuredModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ManualEvaluationCase(StructuredModel):
    question: ShortText
    reference_answer: ShortText
    expected_evidence: list[ShortText] = Field(min_length=1, max_length=4)


class EvaluationRunRequest(StructuredModel):
    mode: Literal["synthetic", "manual"] = "synthetic"
    case_count: int | None = Field(default=None, ge=1, le=12)
    experiments: list[ExperimentConfig] | None = Field(
        default=None, min_length=1, max_length=3
    )
    manual_cases: list[ManualEvaluationCase] | None = Field(
        default=None, min_length=1, max_length=12
    )

    @model_validator(mode="after")
    def validate_mode(self):
        if self.mode == "manual" and not self.manual_cases:
            raise ValueError("manual mode requires manual_cases")
        if self.mode == "synthetic" and self.manual_cases is not None:
            raise ValueError("manual_cases requires manual mode")
        if self.mode == "manual" and self.case_count is not None:
            raise ValueError("case_count applies only to synthetic mode")
        return self


class SourceQuote(StructuredModel):
    chunk_id: str
    quote: ShortText


class SyntheticQuestionCandidate(StructuredModel):
    question: ShortText
    reference_answer: ShortText
    evidence: list[SourceQuote] = Field(min_length=1, max_length=4)


class SyntheticCandidates(StructuredModel):
    cases: list[SyntheticQuestionCandidate] = Field(max_length=2)


class CaseValidation(StructuredModel):
    answerable: bool
    reference_fully_supported: bool
    standalone: bool


class GeneratedAnswer(StructuredModel):
    answer: ShortText
    cited_chunk_ids: list[str]
    insufficient_context: bool


class AnswerClaimVerdict(StructuredModel):
    claim: ShortText
    context_supported: bool
    supporting_chunk_ids: list[str]
    reference_verdict: Literal["matches", "contradicts", "unsupported"]


class ReferenceClaimVerdict(StructuredModel):
    claim: ShortText
    covered: bool


class AnswerJudgeResult(StructuredModel):
    claims: list[AnswerClaimVerdict] = Field(max_length=50)
    reference_claims: list[ReferenceClaimVerdict] = Field(min_length=1, max_length=50)
    relevance_rating: int = Field(ge=0, le=4)
    valid_abstention: bool


class AnswerMetrics(StructuredModel):
    faithfulness: float = Field(ge=0, le=1)
    relevance: float = Field(ge=0, le=1)
    correctness: float = Field(ge=0, le=1)
    hallucination: float = Field(ge=0, le=1)


FailureLabel = Literal[
    "retrieval_failure",
    "low_faithfulness",
    "hallucination",
    "low_correctness",
    "low_relevance",
    "good_result",
]


class QueryFailureAnalysis(StructuredModel):
    evaluation_case_id: int
    question: str
    labels: list[FailureLabel] = Field(min_length=1)
    primary_classification: FailureLabel
    metrics: dict[str, float]
    percentage_metrics: dict[str, str]
    reasons: list[str]


class ConfigurationFailureAnalysis(StructuredModel):
    experiment_name: str
    strategy: str
    configuration: dict
    recommendation_score: float = Field(ge=0, le=1)
    metrics: dict[str, float]
    percentage_metrics: dict[str, str]
    passes_guardrails: bool
    failed_guardrails: list[str]
    failure_counts: dict[str, int]
    failure_rates: dict[str, float]
    per_query_classifications: list[QueryFailureAnalysis]


class EvaluationReport(StructuredModel):
    analysis_version: str
    recommended_experiment: str
    strategy: str
    configuration: dict
    recommendation_score: float = Field(ge=0, le=1)
    percentage_metrics: dict[str, str]
    passes_guardrails: bool
    guardrail_status: str
    why_it_won: str
    key_strengths: list[str]
    key_weaknesses: list[str]
    failure_counts: dict[str, int]
    failure_rates: dict[str, float]
    per_query_classifications: list[QueryFailureAnalysis]
    important_failed_queries: list[QueryFailureAnalysis] = Field(max_length=5)
    practical_next_recommendation: str
    configuration_analyses: list[ConfigurationFailureAnalysis]


class EvaluationSummaryConfiguration(StructuredModel):
    chunk_size: int
    chunk_overlap: int
    top_k: int
    strategy: str


class EvaluationSummaryMetrics(StructuredModel):
    faithfulness: str
    relevance: str
    correctness: str
    hallucination: str
    mrr: str
    recall_at_k: str


class EvaluationRunSummary(StructuredModel):
    recommended_strategy: str
    recommended_experiment: str
    recommendation_score: str
    configuration: EvaluationSummaryConfiguration
    key_metrics: EvaluationSummaryMetrics
    guardrail_status: str
    why_recommended: list[str]
    strengths: list[str]
    weaknesses: list[str]
    next_step: str


class EvaluationRunDetails(StructuredModel):
    project_id: int
    evaluation_dataset_id: int
    dataset_reused: bool
    dataset_mode: str
    case_count: int
    experiment_run_id: int
    best_experiment: dict
    ranking: list[dict]
    report: EvaluationReport


class EvaluationRunResponse(StructuredModel):
    summary: EvaluationRunSummary
    details: EvaluationRunDetails
