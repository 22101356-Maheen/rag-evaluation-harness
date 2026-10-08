from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.auth import get_current_user_id
from backend.app.db.postgres import get_db
from backend.app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
)
from backend.app.services.project_service import (
    create_project,
    get_owned_project_by_id,
    get_projects,
)


router = APIRouter()


# -----------------------------
# Create Project
# -----------------------------

@router.post(
    "/projects",
    response_model=ProjectResponse,
)
def create_new_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    Create a project for the current user.
    """

    return create_project(
        db=db,
        project_data=project_data,
        owner_id=owner_id,
    )


# -----------------------------
# List Projects
# -----------------------------

@router.get(
    "/projects",
    response_model=list[ProjectResponse],
)
def list_projects(
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    Return only projects owned by the current user.
    """

    return get_projects(
        db=db,
        owner_id=owner_id,
    )


# -----------------------------
# Get One Project
# -----------------------------

@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    Return one project only if it belongs to the current user.
    """

    project = get_owned_project_by_id(
        db=db,
        project_id=project_id,
        owner_id=owner_id,
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project