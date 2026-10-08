from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.project import Project
from backend.app.schemas.project import ProjectCreate


def create_project(
    db: Session,
    project_data: ProjectCreate,
    owner_id: str,
) -> Project:
    """
    Create a project for the current user.
    """

    # this connects the new project to its owner.
    project = Project(
        name=project_data.name,
        owner_id=owner_id,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


def get_projects(
    db: Session,
    owner_id: str,
) -> list[Project]:
    """
    Return only projects owned by the current user.
    """

    # this filters projects by owner.
    statement = select(Project).where(
        Project.owner_id == owner_id
    )

    projects = db.scalars(statement).all()

    return list(projects)


def get_project_by_id(
    db: Session,
    project_id: int,
) -> Project | None:
    """
    Return one project by its ID.
    """

    return db.get(Project, project_id)


def get_owned_project_by_id(
    db: Session,
    project_id: int,
    owner_id: str,
) -> Project | None:
    """
    Return a project only if it belongs to the current user.
    """

    # this checks both project ID and owner ID.
    statement = select(Project).where(
        Project.id == project_id,
        Project.owner_id == owner_id,
    )

    return db.scalars(statement).first()