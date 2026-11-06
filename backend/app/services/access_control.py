
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.document import Document
from app.models.permission import (
    DocumentPermission,
    PermissionLevel,
)


def get_document_access(
    db: Session,
    document_id: int,
    current_user: User,
) -> str | None:
    """
    Returns the user's effective document access:
    owner, read, edit, or None.
    """

    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        return None

    # Document owner always retains full control.
    if document.owner_id == current_user.id:
        return "owner"

    # Admin does not automatically bypass document permissions.
    permission = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == document_id,
        DocumentPermission.user_id == current_user.id,
    ).first()

    if not permission:
        return None

    return permission.permission.value


def require_document_read_access(
    db: Session,
    document_id: int,
    current_user: User,
) -> Document:
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    access = get_document_access(
        db, document_id, current_user
    )

    if not document or access not in ("owner", "read", "edit"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to read this document",
        )

    return document


def require_document_edit_access(
    db: Session,
    document_id: int,
    current_user: User,
) -> Document:
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    access = get_document_access(
        db, document_id, current_user
    )

    if not document or access not in ("owner", "edit"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this document",
        )

    return document


def require_document_owner(
    db: Session,
    document_id: int,
    current_user: User,
) -> Document:
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document or document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the document owner can perform this action",
        )

    return document
