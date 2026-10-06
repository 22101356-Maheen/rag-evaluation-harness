from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.postgres import Base

# this file is for blueprinting the project model for the database. It defines the structure of the "projects" table in the PostgreSQL database, including columns for id, name, status, and created_at. The model uses SQLAlchemy's ORM features to map Python classes to database tables, allowing for easy interaction with the database through Python code.

# -----------------------------
# Project Database Model
# -----------------------------

class Project(Base):
    __tablename__ = "projects"

    # This is the unique ID for every project.
    # PostgreSQL automatically gives each new project a new number.
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # This stores the project name entered by the user.
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # This stores the current state of the project.
    # For now every new project starts as "created".
    status: Mapped[str] = mapped_column(
        String(50),
        default="created",
        nullable=False,
    )

    # This stores when the project was created.
    # PostgreSQL automatically sets the current time.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )