from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.postgres import get_db
from backend.app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
)
from backend.app.services.project_service import (
    create_project,
    get_project_by_id,
    get_projects,
)

router = APIRouter()


# -----------------------------
# Project Creation
# -----------------------------

@router.post(
    "/projects",
    response_model=ProjectResponse,
)
def create_new_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Create a new project and save it in PostgreSQL.
    """

    # this sends the validated request to the project service.
    return create_project(
        db=db,
        project_data=project_data,
    )


# -----------------------------
# Project Listing
# -----------------------------

@router.get(
    "/projects",
    response_model=list[ProjectResponse],
)
def list_projects(
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Return all saved projects.
    """

    # this asks the service to read all projects from PostgreSQL.
    return get_projects(
        db=db,
    )


# -----------------------------
# Single Project
# -----------------------------

@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Return one saved project.
    """

    # this asks the service to find the project using its ID.
    project = get_project_by_id(
        db=db,
        project_id=project_id,
    )

    # this returns a clear API error if the project does not exist.
    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project