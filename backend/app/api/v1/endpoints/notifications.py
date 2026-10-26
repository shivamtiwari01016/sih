from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, parse_uuid
from app.models.notification import Notification
from app.models.user import User

router = APIRouter()


def serialize_notification(notification: Notification) -> dict:
    return {
        "id": str(notification.id),
        "type": (
            notification.notification_type.value
            if notification.notification_type
            else None
        ),
        "title": notification.title,
        "message": notification.message,
        "severity": notification.severity.value if notification.severity else None,
        "complaint_id": str(notification.complaint_id) if notification.complaint_id else None,
        "complaint_number": (
            notification.complaint.complaint_number
            if notification.complaint
            else None
        ),
        "read": notification.read_at is not None,
        "created_at": str(notification.created_at) if notification.created_at else None,
        "read_at": str(notification.read_at) if notification.read_at else None,
    }


@router.get("")
def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(
        Notification.recipient_user_id == current_user.id
    )
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return [serialize_notification(n) for n in notifications]


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = (
        db.query(Notification)
        .filter(
            Notification.recipient_user_id == current_user.id,
            Notification.read_at.is_(None),
        )
        .count()
    )
    return {"unread": count}


@router.post("/read-all")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = (
        db.query(Notification)
        .filter(
            Notification.recipient_user_id == current_user.id,
            Notification.read_at.is_(None),
        )
        .update({Notification.read_at: datetime.utcnow()}, synchronize_session=False)
    )
    db.commit()
    return {"message": f"{updated} notification(s) marked as read"}


@router.post("/{id}/read")
def mark_read(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == parse_uuid(id),
            Notification.recipient_user_id == current_user.id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if not notification.read_at:
        notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notification)
    return {"message": "Notification marked as read", "notification": serialize_notification(notification)}
