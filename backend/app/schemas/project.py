from pydantic import BaseModel, ConfigDict, Field


# -----------------------------
# Project Schemas
# -----------------------------

class ProjectCreate(BaseModel):
    # this validates the project name sent by the user.
    name: str = Field(
        min_length=1,
        max_length=200,
    )


class ProjectResponse(BaseModel):
    # this allows Pydantic to read data directly from a SQLAlchemy object.
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    name: str
    status: str