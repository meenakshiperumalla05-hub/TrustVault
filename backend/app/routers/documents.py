
import hashlib
import hmac
import logging
from datetime import date, datetime, time, timedelta
from pathlib import Path

from fastapi import (
    APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.document import Document
from app.models.permission import DocumentPermission, PermissionLevel
from app.models.audit_log import AuditLog, AuditAction
from app.routers.auth import get_current_user
from app.services.file_storage import save_upload
from app.services.access_control import (
    require_document_read_access,
    require_document_edit_access,
    require_document_owner,
)

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)


class ShareRequest(BaseModel):
    user_email: EmailStr
    permission: PermissionLevel


class DocumentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def document_response(document):
    return {
        "id": document.id,
        "name": document.name,
        "description": document.description,
        "category": document.category,
        "file_size": document.file_size,
        "file_hash": document.file_hash,
        "owner_id": document.owner_id,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }


def log_denied(db, user, document, details):
    db.add(AuditLog(
        actor_id=user.id,
        document_id=document.id if document else None,
        action=AuditAction.ACCESS_DENIED,
        status="denied",
        details=details,
    ))
    db.commit()


# 1. UPLOAD DOCUMENT

@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form(...),
    description: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in (UserRole.OWNER, UserRole.ADMIN):
        log_denied(db, current_user, None, "Upload denied: insufficient role")
        raise HTTPException(403, "Only owners can upload documents")

    if not category.strip():
        raise HTTPException(400, "Category is required")

    saved_file = None

    try:
        saved_file = await save_upload(file, settings.storage_path)

        document = Document(
            name=Path(file.filename or "document").name,
            description=description,
            category=category.strip(),
            file_path=saved_file["file_path"],
            content_type=saved_file["content_type"],
            file_size=saved_file["file_size"],
            file_hash=saved_file["file_hash"],
            owner_id=current_user.id,
        )

        db.add(document)
        db.flush()

        db.add(AuditLog(
            actor_id=current_user.id,
            document_id=document.id,
            action=AuditAction.UPLOAD,
            status="success",
            details=f"Uploaded document: {document.name}",
            metadata_json={
                "file_size": document.file_size,
                "file_hash": document.file_hash,
                "category": document.category,
            },
        ))

        db.commit()
        db.refresh(document)

        return {
            "message": "Document uploaded successfully",
            "document": document_response(document),
        }

    except HTTPException:
        db.rollback()
        if saved_file:
            Path(saved_file["file_path"]).unlink(missing_ok=True)
        raise

    except Exception:
        db.rollback()
        if saved_file:
            Path(saved_file["file_path"]).unlink(missing_ok=True)
        logger.exception("Document upload failed")
        raise HTTPException(500, "Document upload failed")

    finally:
        await file.close()


# 2. LIST AND SEARCH DOCUMENTS

@router.get("")
def list_documents(
    q: str | None = Query(None),
    category: str | None = Query(None),
    owner: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(400, "date_from cannot be later than date_to")

    shared_ids = db.query(DocumentPermission.document_id).filter(
        DocumentPermission.user_id == current_user.id
    )

    query = db.query(Document).filter(
        or_(
            Document.owner_id == current_user.id,
            Document.id.in_(shared_ids),
        )
    )

    if q and q.strip():
        query = query.filter(Document.name.ilike(f"%{q.strip()}%"))

    if category and category.strip():
        query = query.filter(
            Document.category.ilike(f"%{category.strip()}%")
        )

    if owner and owner.strip():
        owner_ids = db.query(User.id).filter(
            or_(
                User.full_name.ilike(f"%{owner.strip()}%"),
                User.email.ilike(f"%{owner.strip()}%"),
            )
        )
        query = query.filter(Document.owner_id.in_(owner_ids))

    if date_from:
        query = query.filter(
            Document.created_at >= datetime.combine(date_from, time.min)
        )

    if date_to:
        query = query.filter(
            Document.created_at < datetime.combine(
                date_to + timedelta(days=1), time.min
            )
        )

    total = query.count()
    documents = (
        query.order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "documents": [document_response(doc) for doc in documents],
    }


# 3. GET DOCUMENT DETAILS

@router.get("/{document_id}")
def get_document_details(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    try:
        require_document_read_access(db, document_id, current_user)
    except HTTPException as error:
        if error.status_code == 403:
            log_denied(
                db, current_user, document,
                "Document view denied: insufficient permission",
            )
        raise

    db.add(AuditLog(
        actor_id=current_user.id,
        document_id=document.id,
        action=AuditAction.VIEW,
        status="success",
        details=f"Viewed document details: {document.name}",
    ))
    db.commit()

    return {"document": document_response(document)}


# 4. DOWNLOAD DOCUMENT

@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    try:
        require_document_read_access(db, document_id, current_user)
    except HTTPException as error:
        if error.status_code == 403:
            log_denied(
                db, current_user, document,
                "Download denied: insufficient document permission",
            )
        raise

    file_path = Path(document.file_path)

    if not file_path.is_file():
        db.add(AuditLog(
            actor_id=current_user.id,
            document_id=document.id,
            action=AuditAction.ACCESS_DENIED,
            status="integrity_failed",
            details="Download failed: stored file is missing",
        ))
        db.commit()
        raise HTTPException(404, "Stored file not found")

    sha256 = hashlib.sha256()

    with file_path.open("rb") as stored_file:
        for chunk in iter(lambda: stored_file.read(1024 * 1024), b""):
            sha256.update(chunk)

    actual_hash = sha256.hexdigest()

    if not hmac.compare_digest(actual_hash, document.file_hash):
        db.add(AuditLog(
            actor_id=current_user.id,
            document_id=document.id,
            action=AuditAction.ACCESS_DENIED,
            status="integrity_failed",
            details="Download blocked: SHA-256 hash mismatch",
        ))
        db.commit()
        raise HTTPException(409, "File integrity verification failed")

    db.add(AuditLog(
        actor_id=current_user.id,
        document_id=document.id,
        action=AuditAction.DOWNLOAD,
        status="success",
        details=f"Downloaded document: {document.name}",
        metadata_json={"verified_sha256": actual_hash},
    ))
    db.commit()

    return FileResponse(
        path=str(file_path),
        media_type=document.content_type or "application/octet-stream",
        filename=document.name,
    )


# 5. EDIT DOCUMENT DETAILS

@router.put("/{document_id}")
def update_document(
    document_id: int,
    request: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    try:
        require_document_edit_access(db, document_id, current_user)
    except HTTPException as error:
        if error.status_code == 403:
            log_denied(
                db, current_user, document,
                "Document update denied: edit permission required",
            )
        raise

    changes = request.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(400, "No document changes supplied")

    for field in ("name", "category"):
        if field in changes and (
            changes[field] is None or not changes[field].strip()
        ):
            raise HTTPException(400, f"{field} cannot be empty")

    old_values = {
        key: getattr(document, key)
        for key in changes
    }

    try:
        for key, value in changes.items():
            if key in ("name", "category") and value is not None:
                value = value.strip()
            setattr(document, key, value)

        document.updated_at = datetime.now().astimezone()

        db.add(AuditLog(
            actor_id=current_user.id,
            document_id=document.id,
            action=AuditAction.UPDATE,
            status="success",
            details=f"Updated document details: {document.name}",
            metadata_json={
                "changed_fields": list(changes.keys()),
                "previous_values": old_values,
            },
        ))

        db.commit()
        db.refresh(document)

        return {
            "message": "Document updated successfully",
            "document": document_response(document),
        }

    except Exception:
        db.rollback()
        logger.exception("Document update failed")
        raise HTTPException(500, "Document update failed")


# 6. SHARE DOCUMENT

@router.post("/{document_id}/share")
def share_document(
    document_id: int,
    request: ShareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    try:
        require_document_owner(db, document_id, current_user)
    except HTTPException as error:
        if error.status_code == 403:
            log_denied(
                db, current_user, document,
                "Share denied: document owner permission required",
            )
        raise

    recipient = db.query(User).filter(
        User.email == str(request.user_email).lower()
    ).first()

    if not recipient or not recipient.is_active:
        raise HTTPException(404, "Active recipient account not found")

    if recipient.id == current_user.id:
        raise HTTPException(400, "You cannot share a document with yourself")

    permission = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == document_id,
        DocumentPermission.user_id == recipient.id,
    ).first()

    try:
        if permission:
            permission.permission = request.permission
            permission.granted_by = current_user.id
            permission.granted_at = datetime.now().astimezone()
            message = "Updated document permission"
        else:
            permission = DocumentPermission(
                document_id=document_id,
                user_id=recipient.id,
                permission=request.permission,
                granted_by=current_user.id,
            )
            db.add(permission)
            message = "Granted document permission"

        db.add(AuditLog(
            actor_id=current_user.id,
            document_id=document_id,
            action=AuditAction.PERMISSION_GRANTED,
            status="success",
            details=f"{message} for {recipient.email}: {request.permission.value}",
            metadata_json={
                "recipient_user_id": recipient.id,
                "recipient_email": recipient.email,
                "permission": request.permission.value,
            },
        ))

        db.commit()
        db.refresh(permission)

        return {
            "message": message,
            "document_id": document_id,
            "recipient_email": recipient.email,
            "permission": permission.permission.value,
        }

    except Exception:
        db.rollback()
        logger.exception("Document sharing failed")
        raise HTTPException(500, "Document sharing failed")


# 7. LIST DOCUMENT PERMISSIONS

@router.get("/{document_id}/permissions")
def list_document_permissions(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    try:
        require_document_owner(db, document_id, current_user)
    except HTTPException as error:
        if error.status_code == 403:
            log_denied(
                db, current_user, document,
                "Permission listing denied: owner permission required",
            )
        raise

    permissions = (
        db.query(DocumentPermission, User)
        .join(User, DocumentPermission.user_id == User.id)
        .filter(DocumentPermission.document_id == document_id)
        .all()
    )

    return {
        "document_id": document_id,
        "permissions": [
            {
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "permission": permission.permission.value,
                "granted_by": permission.granted_by,
                "granted_at": permission.granted_at,
            }
            for permission, user in permissions
        ],
    }


# 8. REVOKE DOCUMENT ACCESS

@router.delete("/{document_id}/share/{user_id}")
def revoke_document_access(
    document_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    try:
        require_document_owner(db, document_id, current_user)
    except HTTPException as error:
        if error.status_code == 403:
            log_denied(
                db, current_user, document,
                "Access revocation denied: owner permission required",
            )
        raise

    permission = db.query(DocumentPermission).filter(
        DocumentPermission.document_id == document_id,
        DocumentPermission.user_id == user_id,
    ).first()

    if not permission:
        raise HTTPException(404, "Document permission not found")

    recipient = db.query(User).filter(User.id == user_id).first()
    recipient_email = recipient.email if recipient else None

    try:
        db.delete(permission)

        db.add(AuditLog(
            actor_id=current_user.id,
            document_id=document_id,
            action=AuditAction.PERMISSION_REVOKED,
            status="success",
            details=f"Revoked document access for {recipient_email}",
            metadata_json={
                "recipient_user_id": user_id,
                "recipient_email": recipient_email,
            },
        ))

        db.commit()

        return {
            "message": "Document access revoked successfully",
            "document_id": document_id,
            "user_id": user_id,
        }

    except Exception:
        db.rollback()
        logger.exception("Permission revocation failed")
        raise HTTPException(500, "Permission revocation failed")


# 9. DELETE DOCUMENT

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    try:
        require_document_owner(db, document_id, current_user)
    except HTTPException as error:
        if error.status_code == 403:
            log_denied(
                db, current_user, document,
                "Document deletion denied: owner permission required",
            )
        raise

    file_path = Path(document.file_path)
    document_id_for_audit = document.id
    document_name = document.name

    try:
        db.add(AuditLog(
            actor_id=current_user.id,
            document_id=document_id_for_audit,
            action=AuditAction.DELETE,
            status="success",
            details=f"Deleted document: {document_name}",
            metadata_json={
                "deleted_document_id": document_id_for_audit,
                "deleted_document_name": document_name,
            },
        ))

        db.delete(document)
        db.commit()

        file_path.unlink(missing_ok=True)

        return {
            "message": "Document deleted successfully",
            "document_id": document_id_for_audit,
        }

    except Exception:
        db.rollback()
        logger.exception("Document deletion failed")
        raise HTTPException(500, "Document deletion failed")
