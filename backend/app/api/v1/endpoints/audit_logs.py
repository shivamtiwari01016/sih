import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_auditor
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.utils.helpers import verify_audit_log_integrity

router = APIRouter()


def serialize_log(log: AuditLog) -> dict:
    metadata = None
    if log.sanitized_metadata:
        try:
            metadata = json.loads(log.sanitized_metadata)
        except (ValueError, TypeError):
            metadata = log.sanitized_metadata
    return {
        "id": str(log.id),
        "actor": log.actor.full_name if log.actor else "System",
        "actor_email": log.actor.email if log.actor else None,
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "ip_address": log.ip_address or "127.0.0.1",
        "prev_hash": log.prev_hash,
        "hash": log.hash,
        "metadata": metadata,
        "timestamp": str(log.timestamp) if log.timestamp else None,
    }


@router.get("")
def list_audit_logs(
    limit: int = Query(200, ge=1, le=1000),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auditor),
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action.strip()}%"))
    if entity_type:
        query = query.filter(AuditLog.entity_type.ilike(f"%{entity_type.strip()}%"))
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [serialize_log(log) for log in logs]


@router.get("/verify-integrity")
def check_audit_integrity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cryptographically verify the SHA-256 hash-chain of the audit log."""
    return verify_audit_log_integrity(db)


@router.get("/insider-threats")
def check_insider_threats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scan audit log for unusual volume spikes or off-hours bulk exports (Section 5.G)."""
    # Group views by user
    view_counts = (
        db.query(AuditLog.actor_user_id, func.count(AuditLog.id))
        .filter(AuditLog.action.in_(["VIEW", "BREAK_GLASS_ACCESS", "EXPORT"]))
        .group_by(AuditLog.actor_user_id)
        .all()
    )

    threats = []
    for uid, count in view_counts:
        if uid and count > 30:
            user = db.query(User).filter(User.id == uid).first()
            threats.append({
                "severity": "Medium",
                "officer_name": user.full_name if user else "Unknown Officer",
                "email": user.email if user else "",
                "role": user.role.value if user else "",
                "anomaly": f"High case view volume ({count} views/exports detected)",
                "recommended_action": "Verify justification with bureau head",
            })

    # Break glass count
    bg_logs = db.query(AuditLog).filter(AuditLog.action == "BREAK_GLASS_ACCESS").all()
    for bg in bg_logs:
        threats.append({
            "severity": "High",
            "officer_name": bg.actor.full_name if bg.actor else "Officer",
            "email": bg.actor.email if bg.actor else "",
            "role": bg.actor.role.value if bg.actor else "",
            "anomaly": f"Emergency Break-Glass access exercised for case ID {bg.entity_id}",
            "recommended_action": "Review written regulatory exigency memo",
        })

    return {
        "threats_detected": len(threats),
        "threat_list": threats,
    }
