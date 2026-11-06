
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.routers.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )
    return current_user


@router.get("/audit-logs")
def get_audit_logs(
    actor_id: int | None = Query(None),
    document_id: int | None = Query(None),
    action: str | None = Query(None),
    status: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)

    if actor_id is not None:
        query = query.filter(AuditLog.actor_id == actor_id)

    if document_id is not None:
        query = query.filter(AuditLog.document_id == document_id)

    if action:
        query = query.filter(AuditLog.action == action.upper())

    if status:
        query = query.filter(AuditLog.status == status)

    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)

    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)

    total = query.count()

    logs = (
        query.order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "audit_logs": [
            {
                "id": log.id,
                "actor_id": log.actor_id,
                "document_id": log.document_id,
                "action": log.action.value,
                "status": log.status,
                "details": log.details,
                "ip_address": log.ip_address,
                "metadata": log.metadata_json,
                "created_at": log.created_at,
            }
            for log in logs
        ],
    }
