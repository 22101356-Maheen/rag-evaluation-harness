from pydantic import BaseModel, Field


# -----------------------------
# Project Search Request
# -----------------------------

class ProjectSearchRequest(BaseModel):
    # this is the user's search question.
    query: str = Field(
        min_length=1,
    )

    # this controls how many matching chunks are returned.
    top_k: int = Field(
        default=3,
        ge=1,
        le=20,
    )