from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.project import Project
from backend.app.schemas.project import ProjectCreate


# -----------------------------
# Project Creation
# -----------------------------

def create_project(
    db: Session,
    project_data: ProjectCreate,
) -> Project:
    """
    Create and save a new project in PostgreSQL.
    """

    # this creates a Project object using the validated API data.
    project = Project(
        name=project_data.name,
    )

    # this prepares the new project to be saved in PostgreSQL.
    db.add(project)

    # this permanently saves the project.
    db.commit()

    # this reloads generated values like the project ID.
    db.refresh(project)

    return project


# -----------------------------
# Project Listing
# -----------------------------

def get_projects(
    db: Session,
) -> list[Project]:
    """
    Return all saved projects.
    """

    # this creates a query for all rows in the projects table.
    statement = select(Project)

    # this runs the query and returns all Project objects.
    projects = db.scalars(statement).all()

    return list(projects)


# -----------------------------
# Single Project Lookup
# -----------------------------

def get_project_by_id(
    db: Session,
    project_id: int,
) -> Project | None:
    """
    Return one project using its ID.
    """

    # this searches the projects table by primary key.
    project = db.get(
        Project,
        project_id,
    )

    return project