import csv
import io
import json
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, parse_uuid, require_writer, require_admin
from app.models.bureau import Bureau
from app.models.case_action import CaseAction
from app.models.complaint import Complaint, ComplaintStatus, Priority, Sensitivity
from app.models.institution import Institution
from app.models.related_case import RelatedCase, RelationshipType, ReviewStatus
from app.models.user import User, UserRole
from app.models.action_intent import ActionIntent, IntentType, IntentStatus
from app.models.access_request import AccessRequest, AccessRequestStatus
from app.models.sla_rule import SlaRule
from app.services.matching_service import MatchingService
from app.utils.helpers import (
    encrypt_data,
    decrypt_data,
    generate_pseudo_id,
    notify,
    notify_institution_watchers,
    record_audit,
    record_case_action,
    sanitize_complaint_for_user,
    check_complaint_access,
)

router = APIRouter()
matching_service = MatchingService()


class ComplaintCreate(BaseModel):
    institution_id: str
    received_date: Optional[date] = None
    source_channel: Optional[str] = Field(default=None, max_length=100)
    complainant_reference: Optional[str] = Field(default=None, max_length=255)
    complainant_name: Optional[str] = None
    complainant_contact: Optional[str] = None
    category: str = Field(min_length=2, max_length=100)
    subcategory: Optional[str] = Field(default=None, max_length=100)
    subject: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=5)
    priority: str = "Medium"
    sensitivity: Optional[str] = "Normal"
    assigned_bureau_id: Optional[str] = None
    assigned_officer_id: Optional[str] = None
    expected_disposal_date: Optional[date] = None
    next_action: Optional[str] = Field(default=None, max_length=255)
    # Optional fast Action Intent chip
    action_intent_type: Optional[str] = None
    action_intent_date: Optional[date] = None


class ComplaintUpdate(BaseModel):
    category: Optional[str] = Field(default=None, max_length=100)
    subcategory: Optional[str] = Field(default=None, max_length=100)
    subject: Optional[str] = Field(default=None, min_length=3, max_length=255)
    description: Optional[str] = Field(default=None, min_length=5)
    priority: Optional[str] = None
    sensitivity: Optional[str] = None
    source_channel: Optional[str] = Field(default=None, max_length=100)
    complainant_reference: Optional[str] = Field(default=None, max_length=255)
    next_action: Optional[str] = Field(default=None, max_length=255)
    expected_disposal_date: Optional[date] = None


class ActionCreate(BaseModel):
    action_type: str = Field(default="Case Update", max_length=100)
    remarks: str = Field(min_length=2)
    new_status: Optional[str] = None
    next_action: Optional[str] = Field(default=None, max_length=255)
    expected_disposal_date: Optional[date] = None


class AssignRequest(BaseModel):
    bureau_id: Optional[str] = None
    officer_id: Optional[str] = None
    remarks: Optional[str] = None


class TransferRequest(BaseModel):
    to_bureau_id: str
    reason: str = Field(min_length=3)


class EscalateRequest(BaseModel):
    reason: str = Field(min_length=3)


class DisposeRequest(BaseModel):
    remarks: str = Field(min_length=3)
    disposal_outcome: Optional[str] = Field(default=None, max_length=255)


class PreCheckRequest(BaseModel):
    institution_id: str
    category: str
    subject: Optional[str] = ""
    description: Optional[str] = ""
    assigned_bureau_id: Optional[str] = None


class AccessRequestPayload(BaseModel):
    reason: str = Field(min_length=5)


class BreakGlassPayload(BaseModel):
    reason: str = Field(min_length=10)


class IntentCreatePayload(BaseModel):
    intent_type: str  # Notice, Inspection, Hearing, Penalty, Closure, Transfer
    planned_date: date
    remarks: Optional[str] = None


class IntentResponsePayload(BaseModel):
    verdict: str  # Agreed, Objected, CallMe
    remarks: Optional[str] = None


class EmailInPayload(BaseModel):
    sender: str
    subject: str
    body: str
    institution_name_or_id: Optional[str] = None
    category: Optional[str] = "General"


def parse_priority(value: str) -> Priority:
    if value is None:
        return Priority.MEDIUM
    for priority in Priority:
        if value.strip().lower() in (priority.value.lower(), priority.name.lower()):
            return priority
    raise HTTPException(status_code=400, detail=f"Invalid priority: {value}")


def parse_sensitivity(value: Optional[str]) -> Sensitivity:
    if not value:
        return Sensitivity.NORMAL
    for sens in Sensitivity:
        if value.strip().lower() in (sens.value.lower(), sens.name.lower()):
            return sens
    return Sensitivity.NORMAL


def parse_status(value: str) -> ComplaintStatus:
    if value is None:
        raise HTTPException(status_code=400, detail="Status is required")
    for status in ComplaintStatus:
        if value.strip().lower() in (status.value.lower(), status.name.lower()):
            return status
    raise HTTPException(
        status_code=400,
        detail=f"Invalid status. Allowed: {', '.join(s.value for s in ComplaintStatus)}",
    )


def extract_entities_from_text(text: str) -> Dict[str, Any]:
    """Auto-extract monetary amounts and dates from complaint text."""
    amounts = re.findall(r"(?:Rs\.?|INR|₹)\s*[\d,]+(?:\.\d+)?", text, re.IGNORECASE)
    dates = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text)
    is_hindi = bool(re.search(r"[\u0900-\u097F]", text))
    return {
        "extracted_amounts": amounts,
        "extracted_dates": dates,
        "language": "hi" if is_hindi else "en",
    }


def generate_3line_summary(text: str) -> str:
    """Generate a clean 3-line extractive summary."""
    sentences = [s.strip() for s in re.split(r"[.\n]+", text) if len(s.strip()) > 15]
    if not sentences:
        return text[:150]
    top_sentences = sentences[:3]
    return " ".join(top_sentences)


def get_sla_days_for_category(db: Session, category: str) -> int:
    rule = db.query(SlaRule).filter(SlaRule.category.ilike(category.strip())).first()
    if rule:
        return rule.days_to_dispose
    cat_lower = category.lower()
    if "ragging" in cat_lower or "harassment" in cat_lower:
        return 7
    if "fee" in cat_lower:
        return 30
    if "infra" in cat_lower:
        return 45
    if "exam" in cat_lower:
        return 21
    if "admission" in cat_lower:
        return 14
    return 30


def is_overdue(complaint: Complaint) -> bool:
    return bool(
        complaint.expected_disposal_date
        and complaint.expected_disposal_date < date.today()
        and complaint.current_status not in (ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED)
    )


def serialize_action(action: CaseAction) -> dict:
    return {
        "id": str(action.id),
        "action_type": action.action_type,
        "previous_status": action.previous_status.value if action.previous_status else None,
        "new_status": action.new_status.value if action.new_status else None,
        "remarks": action.remarks,
        "officer": action.officer.full_name if action.officer else None,
        "bureau": action.bureau.bureau_name if action.bureau else None,
        "timestamp": str(action.timestamp) if action.timestamp else None,
        "hash": action.hash,
    }


def serialize_transfer(transfer) -> dict:
    return {
        "id": str(transfer.id),
        "from_bureau": transfer.from_bureau.bureau_name if transfer.from_bureau else None,
        "to_bureau": transfer.to_bureau.bureau_name if transfer.to_bureau else None,
        "reason": transfer.reason,
        "status": transfer.transfer_status.value if transfer.transfer_status else None,
        "requested_by": transfer.requester.full_name if transfer.requester else None,
        "created_at": str(transfer.created_at) if transfer.created_at else None,
    }


def serialize_related(related: RelatedCase, complaint: Complaint) -> dict:
    other = related.complaint_2 if related.complaint_id_1 == complaint.id else related.complaint_1
    return {
        "id": str(related.id),
        "complaint_number": other.complaint_number if other else None,
        "subject": other.subject if other else None,
        "bureau": other.assigned_bureau.bureau_name if other and other.assigned_bureau else None,
        "relationship_type": related.relationship_type.value if related.relationship_type else None,
        "similarity_score": related.similarity_score,
        "review_status": related.review_status.value if related.review_status else None,
        "matching_reasons": json.loads(related.matching_reasons) if related.matching_reasons and related.matching_reasons.startswith("[") else [related.matching_reasons or ""],
    }


def generate_complaint_number(db: Session) -> str:
    year = date.today().year
    prefix = f"CR-{year}-"
    last = (
        db.query(Complaint.complaint_number)
        .filter(Complaint.complaint_number.like(f"{prefix}%"))
        .order_by(Complaint.complaint_number.desc())
        .first()
    )
    sequence = 1
    if last:
        try:
            sequence = int(last[0].split("-")[-1]) + 1
        except (ValueError, IndexError):
            sequence = 1
    candidate = f"{prefix}{sequence:06d}"
    while db.query(Complaint.id).filter(Complaint.complaint_number == candidate).first():
        sequence += 1
        candidate = f"{prefix}{sequence:06d}"
    return candidate


def serialize_complaint(complaint: Complaint, current_user: Optional[User] = None) -> dict:
    if current_user:
        data = sanitize_complaint_for_user(complaint, current_user)
        data["is_overdue"] = is_overdue(complaint)
        data["created_at"] = str(complaint.created_at) if complaint.created_at else None
        return data

    return {
        "id": str(complaint.id),
        "complaint_number": complaint.complaint_number,
        "institution_id": str(complaint.institution_id),
        "institution_name": complaint.institution.institution_name if complaint.institution else None,
        "category": complaint.category,
        "subcategory": complaint.subcategory,
        "subject": complaint.subject,
        "description": complaint.description,
        "summary": complaint.summary,
        "current_status": complaint.current_status.value if complaint.current_status else None,
        "priority": complaint.priority.value if complaint.priority else None,
        "sensitivity": complaint.sensitivity.value if complaint.sensitivity else "Normal",
        "received_date": str(complaint.received_date),
        "source_channel": complaint.source_channel,
        "complainant_reference": complaint.complainant_reference,
        "complainant_pseudo_id": complaint.complainant_pseudo_id,
        "assigned_bureau_id": str(complaint.assigned_bureau_id) if complaint.assigned_bureau_id else None,
        "assigned_bureau": complaint.assigned_bureau.bureau_name if complaint.assigned_bureau else None,
        "assigned_officer_id": str(complaint.assigned_officer_id) if complaint.assigned_officer_id else None,
        "assigned_officer": complaint.assigned_officer.full_name if complaint.assigned_officer else None,
        "expected_disposal_date": str(complaint.expected_disposal_date) if complaint.expected_disposal_date else None,
        "disposed_at": str(complaint.disposed_at) if complaint.disposed_at else None,
        "last_action_at": str(complaint.last_action_at) if complaint.last_action_at else None,
        "next_action": complaint.next_action,
        "is_overdue": is_overdue(complaint),
        "created_at": str(complaint.created_at) if complaint.created_at else None,
    }


# ---------------------------------------------------------------------------
# Pre-Check Live Duplicate/Overlap Banner
# ---------------------------------------------------------------------------
@router.post("/check-overlap-live")
def check_overlap_live(payload: PreCheckRequest, db: Session = Depends(get_db)):
    """Fast pre-save check in <=30s for the live banner before submitting a case."""
    try:
        inst_uuid = parse_uuid(payload.institution_id, "institution id")
    except Exception:
        return {"warnings": []}

    warnings = matching_service.check_pre_save_overlaps(
        db,
        institution_id=inst_uuid,
        category=payload.category,
        subject=payload.subject or "",
        description=payload.description or "",
        bureau_id=parse_uuid(payload.assigned_bureau_id) if payload.assigned_bureau_id else None,
    )
    return {"warnings": warnings, "has_conflicts": len(warnings) > 0}


# ---------------------------------------------------------------------------
# Complaint CRUD & List with ABAC
# ---------------------------------------------------------------------------
@router.get("")
def list_complaints(
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    bureau_id: Optional[str] = None,
    institution_id: Optional[str] = None,
    search: Optional[str] = None,
    overdue_only: bool = False,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint)

    # ABAC: Regional officer restriction
    if current_user and current_user.role == UserRole.REGIONAL_OFFICER:
        reg = (current_user.region_permissions or "").strip().lower()
        if reg and reg != "all":
            query = query.join(Institution, Complaint.institution_id == Institution.id).filter(
                Institution.region.ilike(f"%{reg}%")
            )

    if status:
        query = query.filter(Complaint.current_status == parse_status(status))
    if priority:
        query = query.filter(Complaint.priority == parse_priority(priority))
    if bureau_id:
        query = query.filter(Complaint.assigned_bureau_id == parse_uuid(bureau_id, "bureau id"))
    if institution_id:
        query = query.filter(
            Complaint.institution_id == parse_uuid(institution_id, "institution id")
        )
    if search:
        term = f"%{search.strip()}%"
        query = query.join(Institution, Complaint.institution_id == Institution.id).filter(
            or_(
                Complaint.complaint_number.ilike(term),
                Complaint.subject.ilike(term),
                Complaint.description.ilike(term),
                Complaint.category.ilike(term),
                Institution.institution_name.ilike(term),
            )
        )
    if overdue_only:
        query = query.filter(
            Complaint.expected_disposal_date < date.today(),
            ~Complaint.current_status.in_([ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED]),
        )

    complaints = (
        query.order_by(Complaint.received_date.desc(), Complaint.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [serialize_complaint(c, current_user=current_user) for c in complaints]


@router.post("", status_code=201)
def create_complaint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    institution_uuid = parse_uuid(payload.institution_id, "institution id")
    institution = db.query(Institution).filter(Institution.id == institution_uuid).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    bureau_uuid = None
    if payload.assigned_bureau_id:
        bureau_uuid = parse_uuid(payload.assigned_bureau_id, "bureau id")
        if not db.query(Bureau).filter(Bureau.id == bureau_uuid).first():
            raise HTTPException(status_code=404, detail="Assigned bureau not found")
    elif current_user.bureau_id:
        bureau_uuid = current_user.bureau_id

    officer_uuid = None
    if payload.assigned_officer_id:
        officer_uuid = parse_uuid(payload.assigned_officer_id, "officer id")
        if not db.query(User).filter(User.id == officer_uuid).first():
            raise HTTPException(status_code=404, detail="Assigned officer not found")
    else:
        officer_uuid = current_user.id

    received = payload.received_date or date.today()
    if received > date.today() + timedelta(days=1):
        raise HTTPException(status_code=400, detail="Received date cannot be in the future")

    # SLA-based disposal date
    sla_days = get_sla_days_for_category(db, payload.category)
    expected = payload.expected_disposal_date or (received + timedelta(days=sla_days))

    # Entity extraction and language detection
    full_text = f"{payload.subject} {payload.description}"
    extracted = extract_entities_from_text(full_text)
    summary_text = generate_3line_summary(payload.description)

    # Privacy / Complainant pseudonymisation & AES field-level encryption
    pseudo_id = generate_pseudo_id()
    complainant_cipher = None
    if payload.complainant_name or payload.complainant_contact:
        complainant_cipher = encrypt_data({
            "name": payload.complainant_name or "Anonymous",
            "contact": payload.complainant_contact or "Unspecified",
            "reference": payload.complainant_reference or "",
        })

    complaint = Complaint(
        complaint_number=generate_complaint_number(db),
        institution_id=institution_uuid,
        received_date=received,
        source_channel=(payload.source_channel or "").strip() or "Online Portal",
        complainant_reference=(payload.complainant_reference or "").strip() or None,
        complainant_pseudo_id=pseudo_id,
        complainant_encrypted=complainant_cipher,
        category=payload.category.strip(),
        subcategory=(payload.subcategory or "").strip() or None,
        subject=payload.subject.strip(),
        description=payload.description.strip(),
        summary=summary_text,
        language=extracted["language"],
        priority=parse_priority(payload.priority),
        sensitivity=parse_sensitivity(payload.sensitivity),
        current_status=ComplaintStatus.RECEIVED,
        assigned_bureau_id=bureau_uuid,
        assigned_officer_id=officer_uuid,
        expected_disposal_date=expected,
        next_action=(payload.next_action or "").strip() or "Initial scrutiny",
        created_by=current_user.id,
        last_action_at=datetime.utcnow(),
    )
    db.add(complaint)
    db.flush()

    # Hash-chained initial action
    record_case_action(
        db,
        complaint_id=complaint.id,
        officer=current_user,
        action_type="Registration",
        remarks="Complaint registered under Samanvay",
        previous_status=None,
        new_status=ComplaintStatus.RECEIVED,
        bureau_id=bureau_uuid,
    )

    # Optional fast action intent chip
    if payload.action_intent_type and payload.action_intent_date:
        try:
            intent_enum = IntentType(payload.action_intent_type)
            intent = ActionIntent(
                complaint_id=complaint.id,
                institution_id=institution.id,
                officer_id=current_user.id,
                bureau_id=bureau_uuid,
                intent_type=intent_enum,
                planned_date=payload.action_intent_date,
                status=IntentStatus.PROPOSED,
                remarks="Registered on intake",
            )
            db.add(intent)
        except Exception:
            pass

    # Audit & Notifications
    record_audit(
        db,
        current_user,
        "CREATE",
        "Complaint",
        complaint.id,
        {
            "complaint_number": complaint.complaint_number,
            "institution": institution.institution_name,
            "category": complaint.category,
        },
    )
    notify_institution_watchers(
        db,
        institution.id,
        f"New Complaint on {institution.institution_name}",
        f"Case {complaint.complaint_number} registered under {complaint.category}.",
        exclude_user_id=current_user.id,
        complaint_id=complaint.id,
    )

    db.commit()
    db.refresh(complaint)

    # Overlap engine background scan for newly registered complaint
    suggestions = []
    try:
        from app.services.matching_service import generate_overlaps_for_complaint
        suggestions = generate_overlaps_for_complaint(db, complaint, commit=False)
        db.commit()
    except Exception:
        db.rollback()
        suggestions = []

    if officer_uuid:
        notify(
            db,
            officer_uuid,
            "Assignment",
            "New complaint assigned",
            f"{complaint.complaint_number} - {complaint.subject} has been assigned to you.",
            "Info",
            complaint.id,
        )
        db.commit()

    db.refresh(complaint)
    return {
        **serialize_complaint(complaint, current_user),
        "message": "Complaint registered successfully",
        "overlap_suggestions": len(suggestions),
        "matches": suggestions,
        "extracted_entities": extracted,
    }


@router.post("/{id}/run-matching")
def run_complaint_matching(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    complaint = db.query(Complaint).filter(Complaint.id == parse_uuid(id)).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    from app.services.matching_service import generate_overlaps_for_complaint
    matches = generate_overlaps_for_complaint(db, complaint)
    return {"matches_found": len(matches), "matches": matches}




# ---------------------------------------------------------------------------
# Natural Language Search (Section 5.E)
# ---------------------------------------------------------------------------
@router.get("/nl-search")
def natural_language_search(
    query: str = Query(..., min_length=2),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Parse natural language query into filters (e.g. 'pending fee complaints in Maharashtra older than 30 days')."""
    raw = query.lower()
    filters_applied = {}
    q = db.query(Complaint).join(Institution, Complaint.institution_id == Institution.id)

    # Status parsing
    if "pending" in raw:
        q = q.filter(Complaint.current_status.in_([ComplaintStatus.RECEIVED, ComplaintStatus.UNDER_SCRUTINY, ComplaintStatus.AWAITING_INFORMATION]))
        filters_applied["status"] = "Pending"
    elif "under process" in raw:
        q = q.filter(Complaint.current_status == ComplaintStatus.UNDER_PROCESS)
        filters_applied["status"] = "Under Process"
    elif "disposed" in raw or "closed" in raw:
        q = q.filter(Complaint.current_status.in_([ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED]))
        filters_applied["status"] = "Disposed"

    # Category parsing
    categories = ["fee", "infrastructure", "faculty", "admission", "examination", "affiliation", "ragging", "harassment"]
    for cat in categories:
        if cat in raw:
            q = q.filter(Complaint.category.ilike(f"%{cat}%"))
            filters_applied["category"] = cat.title()
            break

    # State parsing
    states = ["maharashtra", "karnataka", "tamil nadu", "delhi", "uttar pradesh", "gujarat", "punjab", "rajasthan"]
    for st in states:
        if st in raw:
            q = q.filter(Institution.state.ilike(f"%{st}%"))
            filters_applied["state"] = st.title()
            break

    # Age parsing (e.g. "older than 30 days" or "60 days")
    days_match = re.search(r"(\d+)\s*days?", raw)
    if days_match:
        days = int(days_match.group(1))
        cutoff = date.today() - timedelta(days=days)
        q = q.filter(Complaint.received_date <= cutoff)
        filters_applied["older_than_days"] = days

    results = q.limit(50).all()
    count = q.count()

    # Distribution charts
    cat_dist: Dict[str, int] = {}
    state_dist: Dict[str, int] = {}
    for r in results:
        cat_dist[r.category] = cat_dist.get(r.category, 0) + 1
        st = r.institution.state if r.institution and r.institution.state else "Other"
        state_dist[st] = state_dist.get(st, 0) + 1

    return {
        "query": query,
        "filters_applied": filters_applied,
        "total_matches": count,
        "results": [serialize_complaint(c, current_user) for c in results],
        "category_chart": [{"name": k, "count": v} for k, v in cat_dist.items()],
        "state_chart": [{"name": k, "count": v} for k, v in state_dist.items()],
    }


@router.get("/{id}")
def get_complaint(id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    complaint_uuid = parse_uuid(id)
    complaint = db.query(Complaint).filter(Complaint.id == complaint_uuid).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Audit view event
    record_audit(db, current_user, "VIEW", "Complaint", complaint.id)
    db.commit()

    actions = (
        db.query(CaseAction)
        .filter(CaseAction.complaint_id == complaint_uuid)
        .order_by(CaseAction.timestamp.desc())
        .all()
    )
    related = (
        db.query(RelatedCase)
        .filter(
            or_(
                RelatedCase.complaint_id_1 == complaint_uuid,
                RelatedCase.complaint_id_2 == complaint_uuid,
            )
        )
        .all()
    )
    intents = (
        db.query(ActionIntent)
        .filter(ActionIntent.complaint_id == complaint_uuid)
        .order_by(ActionIntent.planned_date.asc())
        .all()
    )

    data = serialize_complaint(complaint, current_user=current_user)
    data.update(
        {
            "institution": {
                "id": str(complaint.institution.id),
                "name": complaint.institution.institution_name,
                "aicte_permanent_id": complaint.institution.aicte_permanent_id,
                "region": complaint.institution.region,
                "state": complaint.institution.state,
                "lat": complaint.institution.lat,
                "lng": complaint.institution.lng,
            },
            "actions": [serialize_action(a) for a in actions],
            "transfers": [serialize_transfer(t) for t in complaint.transfers],
            "related_cases": [serialize_related(r, complaint) for r in related],
            "intents": [
                {
                    "id": str(i.id),
                    "intent_type": i.intent_type.value,
                    "planned_date": i.planned_date.isoformat(),
                    "status": i.status.value,
                    "remarks": i.remarks,
                    "conflicts": json.loads(i.conflicts_json) if i.conflicts_json else [],
                    "officer_name": i.officer.full_name if i.officer else "Officer",
                }
                for i in intents
            ],
        }
    )
    return data


@router.patch("/{id}")
def update_complaint(
    id: str,
    payload: ComplaintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    complaint = db.query(Complaint).filter(Complaint.id == parse_uuid(id)).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    changes = payload.dict(exclude_unset=True)
    if "priority" in changes and changes["priority"]:
        complaint.priority = parse_priority(changes.pop("priority"))
    if "sensitivity" in changes and changes["sensitivity"]:
        complaint.sensitivity = parse_sensitivity(changes.pop("sensitivity"))
    if "expected_disposal_date" in changes and changes["expected_disposal_date"]:
        if changes["expected_disposal_date"] < complaint.received_date:
            raise HTTPException(
                status_code=400,
                detail="Expected disposal date cannot be before the received date",
            )

    for key, value in changes.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(complaint, key, value)

    complaint.last_action_at = datetime.utcnow()
    record_audit(db, current_user, "UPDATE", "Complaint", complaint.id, changes)
    db.commit()
    db.refresh(complaint)
    return {"message": "Complaint updated successfully", **serialize_complaint(complaint, current_user)}


@router.post("/{id}/actions")
def add_action(
    id: str,
    payload: ActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    complaint = db.query(Complaint).filter(Complaint.id == parse_uuid(id)).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    previous_status = complaint.current_status
    new_status = previous_status
    if payload.new_status:
        new_status = parse_status(payload.new_status)

    if payload.expected_disposal_date:
        complaint.expected_disposal_date = payload.expected_disposal_date
    if payload.next_action is not None:
        complaint.next_action = payload.next_action.strip() or None

    complaint.current_status = new_status
    complaint.last_action_at = datetime.utcnow()
    if new_status in (ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED):
        complaint.disposed_at = datetime.utcnow()

    action = record_case_action(
        db,
        complaint_id=complaint.id,
        officer=current_user,
        action_type=payload.action_type.strip() or "Case Update",
        remarks=payload.remarks.strip(),
        previous_status=previous_status,
        new_status=new_status,
        bureau_id=current_user.bureau_id or complaint.assigned_bureau_id,
    )

    record_audit(
        db,
        current_user,
        "CASE_ACTION",
        "Complaint",
        complaint.id,
        {"action_type": action.action_type, "new_status": new_status.value},
    )
    db.commit()
    db.refresh(action)
    return {"message": "Action recorded", "action": serialize_action(action), "complaint": serialize_complaint(complaint, current_user)}


@router.post("/{id}/assign")
def assign_complaint(
    id: str,
    payload: AssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    complaint = db.query(Complaint).filter(Complaint.id == parse_uuid(id)).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if payload.bureau_id:
        bureau_uuid = parse_uuid(payload.bureau_id, "bureau id")
        complaint.assigned_bureau_id = bureau_uuid

    if payload.officer_id:
        officer_uuid = parse_uuid(payload.officer_id, "officer id")
        complaint.assigned_officer_id = officer_uuid

    complaint.current_status = ComplaintStatus.UNDER_PROCESS
    complaint.last_action_at = datetime.utcnow()

    record_case_action(
        db,
        complaint_id=complaint.id,
        officer=current_user,
        action_type="Assignment",
        remarks=(payload.remarks or "Case assigned to officer").strip(),
        previous_status=complaint.current_status,
        new_status=ComplaintStatus.UNDER_PROCESS,
        bureau_id=complaint.assigned_bureau_id,
    )
    record_audit(db, current_user, "ASSIGN", "Complaint", complaint.id)
    db.commit()
    db.refresh(complaint)
    return {"message": "Complaint assigned successfully", **serialize_complaint(complaint, current_user)}


@router.post("/{id}/transfer")
def transfer_complaint(
    id: str,
    payload: TransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    from app.models.bureau_transfer import BureauTransfer, TransferStatus

    complaint = db.query(Complaint).filter(Complaint.id == parse_uuid(id)).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    to_uuid = parse_uuid(payload.to_bureau_id, "to bureau id")
    to_bureau = db.query(Bureau).filter(Bureau.id == to_uuid).first()
    if not to_bureau:
        raise HTTPException(status_code=404, detail="Destination bureau not found")

    from_uuid = complaint.assigned_bureau_id or current_user.bureau_id
    if not from_uuid:
        raise HTTPException(
            status_code=400,
            detail="This complaint has no source bureau. Assign it to a bureau first.",
        )
    if from_uuid == to_uuid:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same bureau")

    transfer = BureauTransfer(
        complaint_id=complaint.id,
        from_bureau_id=from_uuid,
        to_bureau_id=to_uuid,
        requested_by=current_user.id,
        reason=payload.reason.strip(),
        transfer_status=TransferStatus.PENDING,
    )
    db.add(transfer)
    record_case_action(
        db,
        complaint_id=complaint.id,
        officer=current_user,
        action_type="Transfer Requested",
        remarks=f"Transfer to {to_bureau.bureau_name}: {payload.reason.strip()}",
        previous_status=complaint.current_status,
        new_status=complaint.current_status,
    )
    db.commit()
    db.refresh(transfer)
    return {"message": f"Transfer to {to_bureau.bureau_name} requested", "transfer": serialize_transfer(transfer)}


@router.post("/{id}/escalate")
def escalate_complaint(
    id: str,
    payload: EscalateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    complaint = db.query(Complaint).filter(Complaint.id == parse_uuid(id)).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    previous_status = complaint.current_status
    complaint.current_status = ComplaintStatus.ESCALATED
    complaint.priority = Priority.URGENT
    complaint.last_action_at = datetime.utcnow()

    record_case_action(
        db,
        complaint_id=complaint.id,
        officer=current_user,
        action_type="Escalation",
        remarks=f"Case escalated to Senior Management: {payload.reason.strip()}",
        previous_status=previous_status,
        new_status=ComplaintStatus.ESCALATED,
    )
    record_audit(db, current_user, "ESCALATE", "Complaint", complaint.id, {"reason": payload.reason})
    db.commit()
    return {"message": "Case escalated to Senior Management", **serialize_complaint(complaint, current_user)}


@router.post("/{id}/dispose")
def dispose_complaint(
    id: str,
    payload: DisposeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    complaint = db.query(Complaint).filter(Complaint.id == parse_uuid(id)).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    if complaint.current_status in (ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED):
        raise HTTPException(status_code=400, detail="Complaint is already disposed")

    previous_status = complaint.current_status
    complaint.current_status = ComplaintStatus.DISPOSED
    complaint.disposed_at = datetime.utcnow()
    complaint.last_action_at = datetime.utcnow()

    record_case_action(
        db,
        complaint_id=complaint.id,
        officer=current_user,
        action_type="Disposal",
        remarks=f"Disposal Outcome: {payload.disposal_outcome or 'Resolved'} - {payload.remarks.strip()}",
        previous_status=previous_status,
        new_status=ComplaintStatus.DISPOSED,
    )
    record_audit(db, current_user, "DISPOSE", "Complaint", complaint.id)
    db.commit()
    return {"message": "Complaint marked as Disposed", **serialize_complaint(complaint, current_user)}
    return {"message": "Complaint marked as Disposed", **serialize_complaint(complaint, current_user)}


# ---------------------------------------------------------------------------
# Request Access & Break-Glass Protocols
# ---------------------------------------------------------------------------
@router.post("/{id}/request-access")
def request_case_access(
    id: str,
    payload: AccessRequestPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(Complaint.id == parse_uuid(id)).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    req = AccessRequest(
        complaint_id=complaint.id,
        requester_id=current_user.id,
        reason=payload.reason.strip(),
        status=AccessRequestStatus.PENDING,
    )
    db.add(req)
    record_audit(
        db,
        current_user,
        "REQUEST_ACCESS",
        "Complaint",
        complaint.id,
        {"reason": payload.reason},
    )
    if complaint.assigned_officer_id:
        notify(
            db,
            complaint.assigned_officer_id,
            "Transfer Request",
            f"Case Access Request for {complaint.complaint_number}",
            f"{current_user.full_name} ({current_user.role.value}) requested access: {payload.reason}",
            "Warning",
            complaint.id,
        )
    db.commit()
    return {"message": "Access request submitted to case owner", "request_id": str(req.id)}


@router.post("/{id}/break-glass")
def break_glass_access(
    id: str,
    payload: BreakGlassPayload,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Emergency Need-to-Know Break-Glass access for regulatory exigency."""
    complaint = db.query(Complaint).filter(Complaint.id == parse_uuid(id)).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    ip = request.client.host if request.client else "127.0.0.1"

    req = AccessRequest(
        complaint_id=complaint.id,
        requester_id=current_user.id,
        reason=f"[BREAK-GLASS] {payload.reason.strip()}",
        status=AccessRequestStatus.BREAK_GLASS,
        decided_by=current_user.id,
        decided_at=datetime.utcnow(),
    )
    db.add(req)

    # CRITICAL audit entry with IP and written reason
    record_audit(
        db,
        current_user,
        "BREAK_GLASS_ACCESS",
        "Complaint",
        complaint.id,
        {
            "written_reason": payload.reason,
            "ip": ip,
            "case_number": complaint.complaint_number,
            "alert": "EMERGENCY_OVERRIDE_TRIGGERED",
        },
        ip_address=ip,
    )

    # Alert all Auditors & Admins
    auditors = db.query(User).filter(User.role.in_([UserRole.AUDITOR, UserRole.SUPER_ADMIN, UserRole.ADMIN])).all()
    for aud in auditors:
        notify(
            db,
            aud.id,
            "Overdue",
            f"CRITICAL: Break-Glass Access Triggered by {current_user.full_name}",
            f"Emergency access taken for {complaint.complaint_number}. Reason: {payload.reason}",
            "Critical",
            complaint.id,
        )

    db.commit()

    # Return full unmasked L3 data
    full_data = sanitize_complaint_for_user(complaint, current_user, break_glass=True)
    return {
        "message": "Emergency Break-Glass access logged and granted. Auditor alerted.",
        "case": full_data,
    }


# ---------------------------------------------------------------------------
# Action Intent Card: Propose Action & Detect Conflicts
# ---------------------------------------------------------------------------
@router.post("/{id}/intents")
def register_action_intent(
    id: str,
    payload: IntentCreatePayload,
    current_user: User = Depends(require_writer),
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(Complaint.id == parse_uuid(id)).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    intent_type = IntentType(payload.intent_type)

    # Conflict detection against other bureaus' open cases and active intents on this institution
    conflicts = []
    other_cases = (
        db.query(Complaint)
        .filter(
            Complaint.institution_id == complaint.institution_id,
            Complaint.id != complaint.id,
            Complaint.assigned_bureau_id != complaint.assigned_bureau_id,
            Complaint.current_status.in_([ComplaintStatus.RECEIVED, ComplaintStatus.UNDER_PROCESS]),
        )
        .all()
    )
    for oc in other_cases:
        bureau_name = oc.assigned_bureau.bureau_name if oc.assigned_bureau else "Another Bureau"
        conflicts.append(
            f"{bureau_name} has open case {oc.complaint_number} ({oc.category}) targeting closure/hearing."
        )

    other_intents = (
        db.query(ActionIntent)
        .filter(
            ActionIntent.institution_id == complaint.institution_id,
            ActionIntent.complaint_id != complaint.id,
            ActionIntent.status.in_([IntentStatus.PROPOSED, IntentStatus.AGREED]),
        )
        .all()
    )
    for oi in other_intents:
        obureau = oi.bureau.bureau_name if oi.bureau else "Other Bureau"
        conflicts.append(
            f"{obureau} planned {oi.intent_type.value} on {oi.planned_date.strftime('%d %b %Y')}."
        )

    intent = ActionIntent(
        complaint_id=complaint.id,
        institution_id=complaint.institution_id,
        officer_id=current_user.id,
        bureau_id=complaint.assigned_bureau_id,
        intent_type=intent_type,
        planned_date=payload.planned_date,
        status=IntentStatus.PROPOSED,
        conflicts_json=json.dumps(conflicts),
        remarks=payload.remarks,
    )
    db.add(intent)

    # Notify counterpart officers in other bureaus
    for oc in other_cases:
        if oc.assigned_officer_id:
            notify(
                db,
                oc.assigned_officer_id,
                "Transfer Request",
                f"Action Intent Registered: {intent_type.value}",
                f"{current_user.full_name} plans {intent_type.value} on {payload.planned_date} for {complaint.institution.institution_name}.",
                "Warning",
                complaint.id,
            )

    record_audit(
        db,
        current_user,
        "ACTION_INTENT_REGISTERED",
        "ActionIntent",
        intent.id,
        {"type": intent_type.value, "date": str(payload.planned_date), "conflicts": conflicts},
    )
    db.commit()

    return {
        "message": f"Action Intent '{intent_type.value}' registered on institution timeline",
        "intent_id": str(intent.id),
        "conflicts_detected": conflicts,
    }


@router.post("/intents/{intent_id}/respond")
def respond_action_intent(
    intent_id: str,
    payload: IntentResponsePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    intent = db.query(ActionIntent).filter(ActionIntent.id == parse_uuid(intent_id)).first()
    if not intent:
        raise HTTPException(status_code=404, detail="Intent not found")

    if payload.verdict == "Agreed":
        intent.status = IntentStatus.AGREED
    elif payload.verdict == "Objected":
        intent.status = IntentStatus.OBJECTED

    notify(
        db,
        intent.officer_id,
        "Status Change",
        f"Intent Response: {payload.verdict}",
        f"{current_user.full_name} replied '{payload.verdict}' to your planned {intent.intent_type.value}: {payload.remarks or 'No remarks'}",
        "Warning" if payload.verdict == "Objected" else "Info",
        intent.complaint_id,
    )
    record_audit(
        db,
        current_user,
        "ACTION_INTENT_RESPONSE",
        "ActionIntent",
        intent.id,
        {"verdict": payload.verdict, "remarks": payload.remarks},
    )
    db.commit()
    return {"message": f"Response '{payload.verdict}' recorded successfully"}




# ---------------------------------------------------------------------------
# Email-In & Bulk CSV Import (Section 5.D)
# ---------------------------------------------------------------------------
@router.post("/email-in")
def email_in_complaint(
    payload: EmailInPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ingest complaint forwarded by email without double entry."""
    inst = None
    if payload.institution_name_or_id:
        inst = (
            db.query(Institution)
            .filter(
                or_(
                    Institution.institution_name.ilike(f"%{payload.institution_name_or_id}%"),
                    Institution.aicte_permanent_id.ilike(f"%{payload.institution_name_or_id}%"),
                )
            )
            .first()
        )
    if not inst:
        inst = db.query(Institution).first()

    complaint = Complaint(
        complaint_number=generate_complaint_number(db),
        institution_id=inst.id,
        received_date=date.today(),
        source_channel="Forwarded Email",
        complainant_reference=f"Email from {payload.sender}",
        complainant_pseudo_id=generate_pseudo_id(),
        category=payload.category or "General Grievance",
        subject=payload.subject[:250],
        description=payload.body,
        summary=payload.body[:180],
        priority=Priority.MEDIUM,
        current_status=ComplaintStatus.RECEIVED,
        assigned_bureau_id=current_user.bureau_id,
        assigned_officer_id=current_user.id,
        expected_disposal_date=date.today() + timedelta(days=30),
        next_action="Review forwarded email",
        created_by=current_user.id,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return {"message": "Case registered from email", "complaint_number": complaint.complaint_number, "id": str(complaint.id)}


@router.post("/bulk-import")
def bulk_import_complaints(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Bulk import complaints from CSV file."""
    content = file.file.read().decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(content))
    imported = 0
    errors = []

    for row_idx, row in enumerate(reader):
        inst_name = row.get("institution_name") or row.get("institution")
        category = row.get("category") or "General"
        subject = row.get("subject") or "Bulk Imported Complaint"
        description = row.get("description") or subject

        inst = db.query(Institution).filter(Institution.institution_name.ilike(f"%{inst_name}%")).first() if inst_name else None
        if not inst:
            inst = db.query(Institution).first()

        try:
            complaint = Complaint(
                complaint_number=generate_complaint_number(db),
                institution_id=inst.id,
                received_date=date.today(),
                source_channel="CSV Bulk Import",
                complainant_pseudo_id=generate_pseudo_id(),
                category=category,
                subject=subject,
                description=description,
                summary=description[:150],
                priority=Priority.MEDIUM,
                current_status=ComplaintStatus.RECEIVED,
                assigned_bureau_id=current_user.bureau_id,
                assigned_officer_id=current_user.id,
                expected_disposal_date=date.today() + timedelta(days=30),
                created_by=current_user.id,
            )
            db.add(complaint)
            imported += 1
        except Exception as e:
            errors.append(f"Row {row_idx}: {str(e)}")

    db.commit()
    return {"message": f"Bulk import complete: {imported} cases created", "errors": errors}
