from typing import Literal

from pydantic import BaseModel, Field

# -----------------------------
# Search Request Schema
# -----------------------------

class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)
    strategy: Literal[
        "semantic",
        "bm25",
        "hybrid",
    ] = "semantic"