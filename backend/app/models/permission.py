import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PermissionLevel(str, enum.Enum):
    READ = "read"
    EDIT = "edit"


class DocumentPermission(Base):
    __tablename__ = "document_permissions"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "user_id",
            name="uq_document_user_permission",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    permission: Mapped[PermissionLevel] = mapped_column(
        Enum(PermissionLevel, name="permission_level"),
        nullable=False,
    )

    granted_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )