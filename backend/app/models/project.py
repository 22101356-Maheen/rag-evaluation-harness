from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.postgres import Base


class Project(Base):
    __tablename__ = "projects"

    # unique ID for every project.
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # Clerk user ID of the project owner.
    owner_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # project name entered by the user.
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # current state of the project.
    status: Mapped[str] = mapped_column(
        String(50),
        default="created",
        nullable=False,
    )

    # time when the project was created.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )