from pydantic import BaseModel, ConfigDict


# -----------------------------
# Document Response Schema
# -----------------------------

class DocumentResponse(BaseModel):
    # this allows Pydantic to read values from a SQLAlchemy Document object.
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    project_id: int
    filename: str
    status: str