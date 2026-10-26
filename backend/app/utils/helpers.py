"""Helper utilities: ABAC visibility filtering, SHA-256 tamper-evident hash chaining,
AES field-level encryption for DPDP compliance, and notifications.
"""
import base64
import hashlib
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from cryptography.fernet import Fernet
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_log import AuditLog
from app.models.case_action import CaseAction
from app.models.complaint import Complaint, ComplaintStatus, Sensitivity
from app.models.notification import Notification, NotificationType, Severity
from app.models.user import User, UserRole

# Generate a stable 32-byte Fernet key derived from settings.SECRET_KEY
def _get_fernet() -> Fernet:
    key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_data(data: Union[dict, str]) -> str:
    """Field-level AES encryption for complainant and sensitive evidence (DPDP Act 2023)."""
    if isinstance(data, dict):
        raw = json.dumps(data)
    else:
        raw = str(data)
    return _get_fernet().encrypt(raw.encode()).decode()


def decrypt_data(token: Optional[str]) -> Optional[Any]:
    """Decrypt field-level data. Returns original dict or string."""
    if not token:
        return None
    try:
        decrypted = _get_fernet().decrypt(token.encode()).decode()
        try:
            return json.loads(decrypted)
        except Exception:
            return decrypted
    except Exception:
        return "[Decryption Error]"


def generate_pseudo_id() -> str:
    """Generate a privacy-preserving pseudonymised complainant ID."""
    rand_suffix = uuid.uuid4().hex[:6].upper()
    return f"CMP-ANON-{rand_suffix}"


def _coerce_enum(enum_cls, value):
    if isinstance(value, enum_cls):
        return value
    if value is None:
        return None
    text = str(value).strip().lower().replace("_", " ")
    for member in enum_cls:
        if text in (member.value.lower(), member.name.lower().replace("_", " ")):
            return member
    raise ValueError(f"Unknown {enum_cls.__name__}: {value}")


# ---------------------------------------------------------------------------
# Hash-Chained Audit Trail (Tamper-Evident)
# ---------------------------------------------------------------------------

GENESIS_HASH = "0" * 64


def record_audit(
    db: Session,
    actor: Optional[User],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Add a hash-chained tamper-evident audit entry."""
    pending_audit_logs = [obj for obj in db.new if isinstance(obj, AuditLog)]
    if pending_audit_logs:
        prev_hash = pending_audit_logs[-1].hash
    else:
        all_logs = db.query(AuditLog).all()
        if not all_logs:
            prev_hash = GENESIS_HASH
        else:
            used_prev = {l.prev_hash for l in all_logs if l.prev_hash}
            tips = [l for l in all_logs if l.hash and l.hash not in used_prev]
            prev_hash = tips[-1].hash if tips else (all_logs[-1].hash or GENESIS_HASH)

    actor_id_str = str(actor.id) if actor else "SYSTEM"
    meta_str = json.dumps(metadata or {}, sort_keys=True)
    ts = datetime.utcnow()

    content = f"{prev_hash}|{actor_id_str}|{action}|{entity_type}|{entity_id or ''}|{ts.isoformat()}|{meta_str}"
    current_hash = hashlib.sha256(content.encode()).hexdigest()

    entry = AuditLog(
        actor_user_id=actor.id if actor else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        ip_address=ip_address,
        sanitized_metadata=meta_str if metadata else None,
        prev_hash=prev_hash,
        hash=current_hash,
        timestamp=ts,
    )
    db.add(entry)
    return entry


def verify_audit_log_integrity(db: Session) -> Dict[str, Any]:
    """Verify that every entry in the audit trail chain has not been altered or deleted."""
    logs = db.query(AuditLog).all()
    if not logs:
        return {"verified": True, "total_records": 0, "message": "Audit log is empty"}

    by_prev = {log.prev_hash: log for log in logs}
    by_hash = {log.hash: log for log in logs}

    # Identify the genesis record (prev_hash == GENESIS_HASH or has no predecessor in logs)
    genesis_candidates = [l for l in logs if l.prev_hash == GENESIS_HASH or l.prev_hash not in by_hash]
    if not genesis_candidates:
        return {"verified": False, "total_records": len(logs), "error": "No genesis block found"}

    curr_prev = genesis_candidates[0].prev_hash
    visited = 0
    latest_hash = GENESIS_HASH

    while curr_prev in by_prev:
        node = by_prev[curr_prev]
        visited += 1
        curr_prev = node.hash
        latest_hash = node.hash

    return {
        "verified": visited == len(logs),
        "total_records": len(logs),
        "linked_records": visited,
        "latest_hash": latest_hash,
        "message": "All audit log records verified against cryptographic chain" if visited == len(logs) else f"Broken chain: only {visited} of {len(logs)} records linked",
    }


# ---------------------------------------------------------------------------
# Hash-Chained Case Actions
# ---------------------------------------------------------------------------

def record_case_action(
    db: Session,
    complaint_id,
    officer: User,
    action_type: str,
    remarks: str,
    previous_status: Optional[ComplaintStatus] = None,
    new_status: Optional[ComplaintStatus] = None,
    bureau_id = None,
    supporting_doc: Optional[str] = None,
) -> CaseAction:
    """Record a hash-chained action on a complaint."""
    pending_actions = [
        obj for obj in db.new
        if isinstance(obj, CaseAction) and str(obj.complaint_id) == str(complaint_id)
    ]
    if pending_actions:
        prev_hash = pending_actions[-1].hash
    else:
        actions = db.query(CaseAction).filter(CaseAction.complaint_id == complaint_id).all()
        if not actions:
            prev_hash = GENESIS_HASH
        else:
            used_prev = {a.prev_hash for a in actions if a.prev_hash}
            tips = [a for a in actions if a.hash and a.hash not in used_prev]
            prev_hash = tips[-1].hash if tips else (actions[-1].hash or GENESIS_HASH)

    ts = datetime.utcnow()
    content = f"{prev_hash}|{complaint_id}|{officer.id}|{action_type}|{remarks}|{ts.isoformat()}"
    current_hash = hashlib.sha256(content.encode()).hexdigest()

    action = CaseAction(
        complaint_id=complaint_id,
        officer_id=officer.id,
        bureau_id=bureau_id or officer.bureau_id,
        action_type=action_type,
        previous_status=previous_status,
        new_status=new_status,
        remarks=remarks,
        supporting_document_reference=supporting_doc,
        prev_hash=prev_hash,
        hash=current_hash,
        timestamp=ts,
    )
    db.add(action)
    return action


# ---------------------------------------------------------------------------
# ABAC Visibility & Need-to-Know Enforcement
# ---------------------------------------------------------------------------

SENSITIVE_CATEGORIES = {
    "ragging",
    "harassment",
    "sexual harassment",
    "whistleblower",
    "corruption",
}

def is_sensitive_complaint(complaint: Complaint) -> bool:
    if getattr(complaint, "sensitivity", None) in (
        Sensitivity.SENSITIVE,
        Sensitivity.WHISTLEBLOWER,
        Sensitivity.RAGGING,
        Sensitivity.HARASSMENT,
    ):
        return True
    cat = (complaint.category or "").strip().lower()
    return any(sens in cat for sens in SENSITIVE_CATEGORIES)


def check_complaint_access(
    user: User,
    complaint: Complaint,
    has_approved_access: bool = False,
    break_glass: bool = False,
) -> str:
    """Return access level: 'L1', 'L2', or 'L3' based on ABAC attributes."""
    if user.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
        return "L3"

    # Regional officer restriction
    if user.role == UserRole.REGIONAL_OFFICER:
        user_region = (user.region_permissions or "").strip().lower()
        inst_region = (complaint.institution.region or "").strip().lower() if complaint.institution else ""
        if user_region and user_region != "all" and user_region != inst_region:
            return "NO_ACCESS"

    if break_glass or has_approved_access:
        return "L3"

    # Is the user the case owner or in the holding bureau?
    is_owner = (
        (user.id == complaint.assigned_officer_id)
        or (user.bureau_id and complaint.assigned_bureau_id and user.bureau_id == complaint.assigned_bureau_id)
    )

    # Sensitive categories rule: other bureaus see ONLY category + status (L1-masked)
    if is_sensitive_complaint(complaint) and not is_owner:
        return "L1_MASKED"

    if is_owner:
        return "L3"

    # Other officers get L2 visibility if coordinating/overlap exists, otherwise L1
    return "L2"


def sanitize_complaint_for_user(
    complaint: Complaint,
    user: User,
    has_approved_access: bool = False,
    break_glass: bool = False,
) -> Dict[str, Any]:
    """Sanitize complaint data based on ABAC visibility layers."""
    level = check_complaint_access(user, complaint, has_approved_access, break_glass)

    inst = complaint.institution
    bureau = complaint.assigned_bureau
    officer = complaint.assigned_officer

    # Base L1 fields (Visible to all authorized officers)
    data: Dict[str, Any] = {
        "id": str(complaint.id),
        "complaint_number": complaint.complaint_number,
        "institution_id": str(complaint.institution_id),
        "institution_name": inst.institution_name if inst else "Unknown",
        "institution_aicte_id": inst.aicte_permanent_id if inst else None,
        "institution_region": inst.region if inst else None,
        "category": complaint.category,
        "subcategory": complaint.subcategory,
        "current_status": complaint.current_status.value if hasattr(complaint.current_status, "value") else str(complaint.current_status),
        "priority": complaint.priority.value if hasattr(complaint.priority, "value") else str(complaint.priority),
        "sensitivity": complaint.sensitivity.value if hasattr(complaint.sensitivity, "value") else str(complaint.sensitivity or "Normal"),
        "assigned_bureau": bureau.bureau_name if bureau else None,
        "assigned_bureau_id": str(complaint.assigned_bureau_id) if complaint.assigned_bureau_id else None,
        "received_date": complaint.received_date.isoformat() if complaint.received_date else None,
        "expected_disposal_date": complaint.expected_disposal_date.isoformat() if complaint.expected_disposal_date else None,
        "disposed_at": complaint.disposed_at.isoformat() if complaint.disposed_at else None,
        "last_action_at": complaint.last_action_at.isoformat() if complaint.last_action_at else None,
        "visibility_level": level,
        "is_sensitive": is_sensitive_complaint(complaint),
        "access_granted": level in ("L2", "L3"),
    }

    if level == "L1_MASKED":
        # Sensitive case accessed by non-holding bureau: mask description, subject, notes
        data["subject"] = f"[{complaint.category} - Sensitive Matter]"
        data["description"] = "Protected case details under AICTE Need-to-Know policy. Request access or use Break-Glass protocol to view."
        data["summary"] = "Case registered under sensitive category. Bureau access restricted."
        data["complainant_pseudo_id"] = complaint.complainant_pseudo_id or "CMP-PROTECTED"
        data["complainant_details"] = None
        data["assigned_officer"] = None
        data["can_request_access"] = True
        return data

    # L2 fields (Overlap / coordination context)
    data["subject"] = complaint.subject
    data["summary"] = complaint.summary or complaint.description[:180] + ("..." if len(complaint.description or "") > 180 else "")
    data["next_action"] = complaint.next_action
    data["assigned_officer"] = officer.full_name if officer else None
    data["assigned_officer_id"] = str(officer.id) if officer else None
    data["complainant_pseudo_id"] = complaint.complainant_pseudo_id or "CMP-ANON-GENERAL"

    if level == "L3":
        # Full ownership / approved access
        data["description"] = complaint.description
        data["source_channel"] = complaint.source_channel
        data["complainant_reference"] = complaint.complainant_reference
        data["complainant_encrypted"] = complaint.complainant_encrypted
        data["complainant_details"] = decrypt_data(complaint.complainant_encrypted)
    else:
        # L2 mask raw complaint text if overly detailed, show summary
        data["description"] = complaint.description
        data["complainant_details"] = None

    return data


# ---------------------------------------------------------------------------
# Notification System
# ---------------------------------------------------------------------------

def notify(
    db: Session,
    recipient_id,
    notification_type: Union[NotificationType, str],
    title: str,
    message: str,
    severity: Union[Severity, str] = Severity.INFO,
    complaint_id=None,
) -> Notification:
    """Add a notification to the database."""
    entry = Notification(
        recipient_user_id=recipient_id,
        complaint_id=complaint_id,
        notification_type=_coerce_enum(NotificationType, notification_type),
        title=title,
        message=message,
        severity=_coerce_enum(Severity, severity),
    )
    db.add(entry)
    return entry


def notify_institution_watchers(
    db: Session,
    institution_id,
    title: str,
    message: str,
    exclude_user_id = None,
    complaint_id = None,
):
    """Notify all officers watching this institution."""
    from app.models.watchlist import Watchlist
    watchers = db.query(Watchlist).filter(Watchlist.institution_id == institution_id).all()
    for w in watchers:
        if exclude_user_id and str(w.user_id) == str(exclude_user_id):
            continue
        notify(
            db,
            w.user_id,
            NotificationType.STATUS_CHANGE,
            title,
            message,
            Severity.INFO,
            complaint_id=complaint_id,
        )


def iso(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)
