import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, parse_uuid, require_writer
from app.models.complaint import Complaint, ComplaintStatus, Priority
from app.models.institution import Institution
from app.models.related_case import RelatedCase, ReviewStatus
from app.models.user import User
from app.models.watchlist import Watchlist
from app.utils.helpers import record_audit

router = APIRouter()


class InstitutionCreate(BaseModel):
    institution_name: str = Field(min_length=2, max_length=255)
    aicte_permanent_id: Optional[str] = Field(default=None, max_length=100)
    institution_type: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    contact_email: Optional[str] = Field(default=None, max_length=255)
    website: Optional[str] = Field(default=None, max_length=255)
    established_year: Optional[int] = Field(default=None, ge=1800, le=2100)
    ownership: Optional[str] = Field(default=None, max_length=100)
    affiliation: Optional[str] = Field(default=None, max_length=255)
    lat: Optional[float] = None
    lng: Optional[float] = None
    aliases: Optional[str] = None


class InstitutionUpdate(BaseModel):
    institution_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    aicte_permanent_id: Optional[str] = Field(default=None, max_length=100)
    institution_type: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    district: Optional[str] = Field(default=None, max_length=100)
    contact_email: Optional[str] = Field(default=None, max_length=255)
    website: Optional[str] = Field(default=None, max_length=255)
    established_year: Optional[int] = Field(default=None, ge=1800, le=2100)
    ownership: Optional[str] = Field(default=None, max_length=100)
    affiliation: Optional[str] = Field(default=None, max_length=255)
    institution_status: Optional[str] = Field(default=None, max_length=50)
    lat: Optional[float] = None
    lng: Optional[float] = None


def compute_risk_score(inst: Institution, db: Session) -> dict:
    """Compute explainable 0-100 institution risk score with factor breakdown."""
    complaints = db.query(Complaint).filter(Complaint.institution_id == inst.id).all()
    total = len(complaints)
    open_cases = [c for c in complaints if c.current_status not in (ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED)]
    overdue = [c for c in open_cases if c.expected_disposal_date and c.expected_disposal_date < date.today()]
    high_priority = [c for c in complaints if c.priority in (Priority.HIGH, Priority.URGENT)]

    # Overlaps on this institution
    overlap_count = (
        db.query(RelatedCase)
        .join(Complaint, or_(RelatedCase.complaint_id_1 == Complaint.id, RelatedCase.complaint_id_2 == Complaint.id))
        .filter(Complaint.institution_id == inst.id, RelatedCase.review_status == ReviewStatus.SUGGESTED)
        .count()
    )

    factors = []
    score = 0

    # Factor 1: Repeat complaints
    if total > 5:
        repeat_pts = min(total * 4, 30)
        score += repeat_pts
        factors.append({"factor": "Repeat Complaints", "points": repeat_pts, "description": f"{total} total complaints on record"})

    # Factor 2: Overdue / Aging cases
    if overdue:
        overdue_pts = min(len(overdue) * 10, 25)
        score += overdue_pts
        factors.append({"factor": "Overdue Cases", "points": overdue_pts, "description": f"{len(overdue)} cases past SLA deadline"})

    # Factor 3: High/Urgent Severity
    if high_priority:
        sev_pts = min(len(high_priority) * 6, 20)
        score += sev_pts
        factors.append({"factor": "High Severity Matters", "points": sev_pts, "description": f"{len(high_priority)} high/urgent severity cases"})

    # Factor 4: Active Overlaps
    if overlap_count > 0:
        score += 15
        factors.append({"factor": "Cross-Bureau Overlap", "points": 15, "description": "Active overlap between Regulation Bureau and PGRC"})

    final_score = min(score, 100)
    level = "Low" if final_score < 35 else ("Medium" if final_score < 70 else "High")

    return {
        "risk_score": final_score,
        "risk_level": level,
        "factor_breakdown": factors,
        "total_complaints": total,
        "open_complaints": len(open_cases),
        "overdue_complaints": len(overdue),
        "active_overlaps": overlap_count,
    }


def serialize_institution(inst: Institution, complaint_count: int = 0) -> dict:
    return {
        "id": str(inst.id),
        "institution_name": inst.institution_name,
        "aicte_permanent_id": inst.aicte_permanent_id,
        "institution_type": inst.institution_type,
        "address": inst.address,
        "city": inst.city,
        "state": inst.state,
        "region": inst.region,
        "district": inst.district,
        "contact_email": inst.contact_email,
        "website": inst.website,
        "established_year": inst.established_year,
        "ownership": inst.ownership,
        "affiliation": inst.affiliation,
        "institution_status": inst.institution_status,
        "lat": inst.lat,
        "lng": inst.lng,
        "complaint_count": complaint_count,
        "created_at": str(inst.created_at) if inst.created_at else None,
    }


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


@router.get("/compare")
def compare_institutions(
    id1: str = Query(..., description="First institution ID"),
    id2: str = Query(..., description="Second institution ID"),
    db: Session = Depends(get_db),
):
    """Side-by-side comparison of two institutions (Section 5.F)."""
    inst1 = db.query(Institution).filter(Institution.id == parse_uuid(id1)).first()
    inst2 = db.query(Institution).filter(Institution.id == parse_uuid(id2)).first()
    if not inst1 or not inst2:
        raise HTTPException(status_code=404, detail="One or both institutions not found")

    risk1 = compute_risk_score(inst1, db)
    risk2 = compute_risk_score(inst2, db)

    return {
        "institution_1": {**serialize_institution(inst1, risk1["total_complaints"]), "risk": risk1},
        "institution_2": {**serialize_institution(inst2, risk2["total_complaints"]), "risk": risk2},
    }


@router.get("")
def list_institutions(
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=1000),
    search: Optional[str] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Institution)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            (Institution.institution_name.ilike(term))
            | (Institution.aicte_permanent_id.ilike(term))
            | (Institution.city.ilike(term))
            | (Institution.aliases.ilike(term))
        )
    if region:
        query = query.filter(Institution.region == region)

    institutions = (
        query.order_by(Institution.institution_name.asc()).offset(skip).limit(limit).all()
    )

    ids = [i.id for i in institutions]
    counts = {}
    if ids:
        counts = dict(
            db.query(Complaint.institution_id, func.count(Complaint.id))
            .filter(Complaint.institution_id.in_(ids))
            .group_by(Complaint.institution_id)
            .all()
        )

    return [serialize_institution(i, counts.get(i.id, 0)) for i in institutions]


@router.post("", status_code=201)
def create_institution(
    inst: InstitutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    name = inst.institution_name.strip()
    normalized = name.lower()
    if not normalized:
        raise HTTPException(status_code=400, detail="Institution name is required")

    duplicate = db.query(Institution).filter(Institution.normalized_name == normalized).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="An institution with this name already exists")

    aicte_id = _clean(inst.aicte_permanent_id)
    if aicte_id:
        existing = db.query(Institution).filter(Institution.aicte_permanent_id == aicte_id).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail="An institution with this AICTE permanent ID already exists",
            )

    new_inst = Institution(
        institution_name=name,
        normalized_name=normalized,
        aicte_permanent_id=aicte_id,
        institution_type=_clean(inst.institution_type),
        address=_clean(inst.address),
        city=_clean(inst.city),
        state=_clean(inst.state),
        region=_clean(inst.region),
        district=_clean(inst.district),
        contact_email=_clean(inst.contact_email),
        website=_clean(inst.website),
        established_year=inst.established_year,
        ownership=_clean(inst.ownership),
        affiliation=_clean(inst.affiliation),
        lat=inst.lat,
        lng=inst.lng,
        institution_status="Active",
    )
    db.add(new_inst)
    try:
        db.flush()
        record_audit(
            db,
            current_user,
            "CREATE",
            "Institution",
            new_inst.id,
            {"institution_name": name, "aicte_permanent_id": aicte_id},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Institution could not be created (duplicate data)")
    db.refresh(new_inst)
    return {
        **serialize_institution(new_inst),
        "message": "Institution created successfully",
    }


@router.get("/{id}")
def get_institution(id: str, db: Session = Depends(get_db)):
    inst = db.query(Institution).filter(Institution.id == parse_uuid(id)).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    count = db.query(func.count(Complaint.id)).filter(Complaint.institution_id == inst.id).scalar() or 0
    risk = compute_risk_score(inst, db)
    data = serialize_institution(inst, count)
    data["risk"] = risk
    return data


@router.get("/{id}/risk-score")
def get_institution_risk_score(id: str, db: Session = Depends(get_db)):
    """Explainable risk score breakdown."""
    inst = db.query(Institution).filter(Institution.id == parse_uuid(id)).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    return compute_risk_score(inst, db)


@router.post("/{id}/watch")
def watch_institution(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add institution to current user's watchlist."""
    inst = db.query(Institution).filter(Institution.id == parse_uuid(id)).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    existing = db.query(Watchlist).filter(Watchlist.user_id == current_user.id, Watchlist.institution_id == inst.id).first()
    if not existing:
        w = Watchlist(user_id=current_user.id, institution_id=inst.id)
        db.add(w)
        db.commit()
    return {"message": f"Now watching {inst.institution_name}", "watching": True}


@router.delete("/{id}/watch")
def unwatch_institution(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove institution from user's watchlist."""
    inst_uuid = parse_uuid(id)
    db.query(Watchlist).filter(Watchlist.user_id == current_user.id, Watchlist.institution_id == inst_uuid).delete()
    db.commit()
    return {"message": "Unwatched institution", "watching": False}


@router.get("/{id}/is-watched")
def is_institution_watched(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inst_uuid = parse_uuid(id)
    watched = bool(db.query(Watchlist).filter(Watchlist.user_id == current_user.id, Watchlist.institution_id == inst_uuid).first())
    return {"watching": watched}


@router.patch("/{id}")
def update_institution(
    id: str,
    payload: InstitutionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    inst = db.query(Institution).filter(Institution.id == parse_uuid(id)).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    changes = payload.dict(exclude_unset=True)
    if "institution_name" in changes:
        name = (changes["institution_name"] or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Institution name is required")
        normalized = name.lower()
        duplicate = (
            db.query(Institution)
            .filter(Institution.normalized_name == normalized, Institution.id != inst.id)
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=409, detail="An institution with this name already exists")
        changes["institution_name"] = name
        changes["normalized_name"] = normalized

    for key, value in changes.items():
        setattr(inst, key, value)

    try:
        record_audit(db, current_user, "UPDATE", "Institution", inst.id, changes)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Institution could not be updated (duplicate data)")
    return {"message": "Institution updated successfully", **serialize_institution(inst)}


@router.get("/{id}/complaints")
def get_institution_complaints(
    id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    institution_uuid = parse_uuid(id)
    inst = db.query(Institution).filter(Institution.id == institution_uuid).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    complaints = (
        db.query(Complaint)
        .filter(Complaint.institution_id == institution_uuid)
        .order_by(Complaint.received_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(c.id),
            "complaint_number": c.complaint_number,
            "subject": c.subject,
            "category": c.category,
            "current_status": c.current_status.value if c.current_status else None,
            "priority": c.priority.value if c.priority else None,
            "received_date": str(c.received_date),
            "assigned_bureau": c.assigned_bureau.bureau_name if c.assigned_bureau else None,
        }
        for c in complaints
    ]
