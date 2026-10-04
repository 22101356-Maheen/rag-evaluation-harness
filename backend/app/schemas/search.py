from pydantic import BaseModel, Field

# -----------------------------
# Search Request Schema
# -----------------------------

class SearchRequest(BaseModel):
    """
    Schema for the search request.
    """
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)