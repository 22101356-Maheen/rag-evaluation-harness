from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.postgres import Base


# -----------------------------
# Document Model
# -----------------------------

class Document(Base):
    __tablename__ = "documents"

    # this is the unique ID for every uploaded document.
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # this connects the document to its parent project.
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
    )

    # this stores the original uploaded file name.
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # this stores the current processing state of the document.
    status: Mapped[str] = mapped_column(
        String(50),
        default="uploaded",
        nullable=False,
    )

    # this stores when the document was added.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )