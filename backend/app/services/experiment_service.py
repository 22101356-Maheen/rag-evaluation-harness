from pathlib import Path

from backend.app.db.qdrant import store_chunks
from backend.app.rag.chunking.text_chunker import chunk_text
from backend.app.rag.embeddings.embedder import embed_texts
from backend.app.schemas.experiment import ExperimentConfig
from backend.app.services.evaluation_service import evaluate_retrieval

# -----------------------------
# Experiment Data Source
# -----------------------------

CORPUS_PATH = Path(
    "data/evaluation/rag_retrieval_corpus.txt"
)


# -----------------------------
# Corpus Loading
# -----------------------------

def load_experiment_corpus() -> str:
    """
    Load the source corpus used for retrieval experiments.
    """

    return CORPUS_PATH.read_text(
        encoding="utf-8",
    )


# -----------------------------
# Single Experiment Execution
# -----------------------------

def run_experiment(
    config: ExperimentConfig,
) -> dict:
    """
    Run one retrieval experiment using the supplied configuration.
    """

    corpus = load_experiment_corpus()

    chunks = chunk_text(
        text=corpus,
        chunk_size=config.chunk_size,
        overlap=config.chunk_overlap,
    )

    embeddings = embed_texts(chunks)

    store_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    evaluation = evaluate_retrieval(
        top_k=config.top_k,
    )

    return {
        "experiment_name": config.name,
        "configuration": {
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "top_k": config.top_k,
            "strategy": config.strategy,
        },
        "chunk_count": len(chunks),
        "evaluation": evaluation,
    }


# -----------------------------
# Strategy Summary
# -----------------------------

def get_strategy_summary(
    experiment_result: dict,
    strategy: str,
) -> dict:
    """
    Extract the selected strategy's main evaluation metrics.
    """

    strategy_metrics = experiment_result[
        "evaluation"
    ][
        "strategies"
    ][
        strategy
    ]

    return {
        "hit_at_k": strategy_metrics["average_hit_at_k"],
        "precision_at_k": strategy_metrics["average_precision_at_k"],
        "recall_at_k": strategy_metrics["average_recall_at_k"],
        "mrr": strategy_metrics["mean_reciprocal_rank"],
    }


# -----------------------------
# Batch Experiment Execution
# -----------------------------

def run_experiment_batch(
    configs: list[ExperimentConfig],
) -> dict:
    """
    Run multiple RAG configurations and return a ranked summary.
    """

    summaries = []

    for config in configs:
        result = run_experiment(config)

        metrics = get_strategy_summary(
            experiment_result=result,
            strategy=config.strategy,
        )

        summaries.append(
            {
                "experiment_name": config.name,
                "configuration": result["configuration"],
                "chunk_count": result["chunk_count"],
                "metrics": metrics,
                "score": metrics["mrr"],
            }
        )

    ranked_results = sorted(
        summaries,
        key=lambda item: item["score"],
        reverse=True,
    )

    best_experiment = ranked_results[0]

    return {
        "experiment_count": len(ranked_results),
        "best_experiment": best_experiment,
        "ranking": ranked_results,
    }