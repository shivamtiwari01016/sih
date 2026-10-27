import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_current_user_optional, parse_uuid, require_writer
from app.models.case_action import CaseAction
from app.models.complaint import Complaint, ComplaintStatus, Priority, Sensitivity
from app.models.institution import Institution
from app.models.related_case import RelatedCase, ReviewStatus
from app.models.user import User, UserRole
from app.models.watchlist import Watchlist
from app.utils.helpers import record_audit
from app.api.v1.endpoints.overlaps import serialize_overlap

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
    current_user: Optional[User] = Depends(get_current_user_optional),
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

    results = []
    for c in complaints:
        # ABAC for sensitive complaints: mask subject if not holding bureau and not admin
        has_access = True
        is_sensitive = c.sensitivity and c.sensitivity != Sensitivity.NORMAL
        if is_sensitive and current_user:
            if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.AUDITOR):
                if not (c.assigned_bureau_id and current_user.bureau_id and str(c.assigned_bureau_id) == str(current_user.bureau_id)):
                    has_access = False
        elif is_sensitive and not current_user:
            has_access = False

        subject = c.subject if has_access else f"[{c.category} - Sensitive Matter]"
        results.append({
            "id": str(c.id),
            "complaint_number": c.complaint_number,
            "subject": subject,
            "category": c.category,
            "current_status": c.current_status.value if c.current_status else None,
            "priority": c.priority.value if c.priority else None,
            "received_date": str(c.received_date),
            "assigned_bureau": c.assigned_bureau.bureau_name if c.assigned_bureau else None,
            "is_sensitive": is_sensitive,
        })
    return results


@router.get("/{id}/eda")
def get_institution_eda(
    id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Exploratory Data Analysis (EDA) and trends for an institution."""
    inst_uuid = parse_uuid(id)
    inst = db.query(Institution).filter(Institution.id == inst_uuid).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    complaints = db.query(Complaint).filter(Complaint.institution_id == inst_uuid).all()
    total = len(complaints)
    today = date.today()

    open_complaints = [
        c for c in complaints
        if c.current_status not in (ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED)
    ]
    disposed_complaints = [
        c for c in complaints
        if c.current_status in (ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED)
    ]
    overdue_complaints = [
        c for c in open_complaints
        if c.expected_disposal_date and c.expected_disposal_date < today
    ]

    inst_comp_ids = [c.id for c in complaints]
    active_overlaps = 0
    if inst_comp_ids:
        active_overlaps = (
            db.query(RelatedCase)
            .filter(
                or_(
                    RelatedCase.complaint_id_1.in_(inst_comp_ids),
                    RelatedCase.complaint_id_2.in_(inst_comp_ids),
                ),
                RelatedCase.review_status.in_([
                    ReviewStatus.SUGGESTED,
                    ReviewStatus.ACKNOWLEDGED,
                    ReviewStatus.COORDINATING,
                    ReviewStatus.REQUIRES_FURTHER_REVIEW,
                ]),
            )
            .count()
        )

    if open_complaints:
        ages = [(today - c.received_date).days for c in open_complaints if c.received_date]
        avg_open_age_days = round(sum(ages) / len(ages), 1) if ages else 0.0
    else:
        avg_open_age_days = 0.0

    stats = {
        "total": total,
        "open": len(open_complaints),
        "overdue": len(overdue_complaints),
        "disposed": len(disposed_complaints),
        "active_overlaps": active_overlaps,
        "avg_open_age_days": avg_open_age_days,
    }

    # Monthly trends (last 12 months)
    monthly = []
    for i in range(11, -1, -1):
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1
        month_label = date(y, m, 1).strftime("%b %Y")
        rec_count = sum(
            1 for c in complaints
            if c.received_date and c.received_date.year == y and c.received_date.month == m
        )
        disp_count = sum(
            1 for c in disposed_complaints
            if (c.disposed_at and c.disposed_at.year == y and c.disposed_at.month == m)
            or (not c.disposed_at and c.last_action_at and c.last_action_at.year == y and c.last_action_at.month == m)
        )
        monthly.append({
            "month": month_label,
            "received": rec_count,
            "disposed": disp_count,
        })

    # By category
    cat_counts: dict[str, int] = {}
    for c in complaints:
        cat = c.category or "Other"
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    by_category = [{"category": k, "count": v} for k, v in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)]

    # By bureau
    bureau_counts: dict[str, int] = {}
    for c in complaints:
        b_name = c.assigned_bureau.bureau_name if c.assigned_bureau else "Unassigned"
        bureau_counts[b_name] = bureau_counts.get(b_name, 0) + 1
    by_bureau = [{"bureau": k, "count": v} for k, v in sorted(bureau_counts.items(), key=lambda x: x[1], reverse=True)]

    # By status
    status_counts: dict[str, int] = {}
    for c in complaints:
        st_val = c.current_status.value if c.current_status else "Received"
        status_counts[st_val] = status_counts.get(st_val, 0) + 1
    by_status = [{"status": k, "count": v} for k, v in sorted(status_counts.items(), key=lambda x: x[1], reverse=True)]

    # Ageing buckets for open cases
    ageing = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
    for c in open_complaints:
        if c.received_date:
            d = (today - c.received_date).days
            if d <= 30:
                ageing["0-30"] += 1
            elif d <= 60:
                ageing["31-60"] += 1
            elif d <= 90:
                ageing["61-90"] += 1
            else:
                ageing["90+"] += 1

    # SLA metrics
    if disposed_complaints:
        within_sla_disposed = sum(
            1 for c in disposed_complaints
            if not c.expected_disposal_date or (c.disposed_at and c.disposed_at.date() <= c.expected_disposal_date)
        )
        within_sla_pct = round((within_sla_disposed / len(disposed_complaints)) * 100.0, 1)
    elif total > 0:
        non_overdue = total - len(overdue_complaints)
        within_sla_pct = round((non_overdue / total) * 100.0, 1)
    else:
        within_sla_pct = 100.0

    total_all = db.query(func.count(Complaint.id)).scalar() or 1
    overdue_all = db.query(func.count(Complaint.id)).filter(
        Complaint.current_status.notin_([ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED]),
        Complaint.expected_disposal_date < today
    ).scalar() or 0
    all_institutions_avg_pct = round(((total_all - overdue_all) / total_all) * 100.0, 1)

    sla = {
        "within_sla_pct": within_sla_pct,
        "all_institutions_avg_pct": all_institutions_avg_pct,
    }

    # Peer metrics
    if inst.state:
        peer_insts = db.query(Institution).filter(Institution.state == inst.state).all()
    else:
        peer_insts = [inst]
    peer_ids = [p.id for p in peer_insts]
    peer_counts = dict(
        db.query(Complaint.institution_id, func.count(Complaint.id))
        .filter(Complaint.institution_id.in_(peer_ids))
        .group_by(Complaint.institution_id)
        .all()
    )
    counts_list = [peer_counts.get(pid, 0) for pid in peer_ids]
    state_avg_count = round(sum(counts_list) / max(len(counts_list), 1), 1)
    state_avg_risk = round(sum(min(int(cnt * 12 + 10), 100) for cnt in counts_list) / max(len(counts_list), 1), 1)

    peer = {
        "institution_count": total,
        "state_avg_count": state_avg_count,
        "state_avg_risk": state_avg_risk,
    }

    # Dynamic Insights (max 4)
    insights = []
    if by_category:
        top_cat = by_category[0]["category"]
        top_cnt = by_category[0]["count"]
        top_pct = round((top_cnt / max(total, 1)) * 100, 1)
        insights.append(f"'{top_cat}' is the primary category, representing {top_pct}% of complaints ({top_cnt} cases).")

    if active_overlaps > 0:
        insights.append(f"{active_overlaps} active cross-bureau overlap(s) requiring coordinated investigation.")
    else:
        insights.append("Zero active jurisdictional conflicts detected across open files.")

    if open_complaints:
        insights.append(f"Open cases average {avg_open_age_days} days in queue (SLA threshold: 30 days).")
    else:
        insights.append("All complaints on record have been successfully disposed.")

    if total >= state_avg_count:
        ratio = round(total / max(state_avg_count, 1), 1)
        insights.append(f"Complaint volume is {ratio}x the {inst.state or 'regional'} state peer average ({state_avg_count} cases).")
    else:
        insights.append(f"Complaint volume is within the {inst.state or 'regional'} state peer average ({state_avg_count} cases).")

    insights = insights[:4]
    insufficient_data = total < 5

    return {
        "institution_id": str(inst.id),
        "institution_name": inst.institution_name,
        "insufficient_data": insufficient_data,
        "stats": stats,
        "monthly": monthly,
        "by_category": by_category,
        "by_bureau": by_bureau,
        "by_status": by_status,
        "ageing": ageing,
        "sla": sla,
        "peer": peer,
        "insights": insights,
    }


@router.get("/{id}/overlaps")
def get_institution_overlaps(
    id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve all cross-bureau and duplicate overlaps involving complaints of this institution."""
    inst_uuid = parse_uuid(id)
    complaint_ids = [c.id for c in db.query(Complaint.id).filter(Complaint.institution_id == inst_uuid).all()]
    if not complaint_ids:
        return []
    overlaps = (
        db.query(RelatedCase)
        .filter(
            or_(
                RelatedCase.complaint_id_1.in_(complaint_ids),
                RelatedCase.complaint_id_2.in_(complaint_ids),
            )
        )
        .order_by(RelatedCase.created_at.desc())
        .all()
    )
    return [serialize_overlap(o) for o in overlaps]


@router.get("/{id}/timeline")
def get_institution_timeline(
    id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Merged chronological regulatory case actions across all bureaus for this institution."""
    inst_uuid = parse_uuid(id)
    actions = (
        db.query(CaseAction)
        .join(Complaint, CaseAction.complaint_id == Complaint.id)
        .filter(Complaint.institution_id == inst_uuid)
        .order_by(CaseAction.timestamp.desc())
        .limit(100)
        .all()
    )
    res = []
    for a in actions:
        c = a.complaint
        is_sensitive = c and c.sensitivity != Sensitivity.NORMAL
        has_access = True
        if is_sensitive and current_user:
            if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.AUDITOR):
                if not (c.assigned_bureau_id and current_user.bureau_id and str(c.assigned_bureau_id) == str(current_user.bureau_id)):
                    has_access = False
        elif is_sensitive and not current_user:
            has_access = False

        remarks = a.remarks if has_access else "Action details restricted under Need-to-Know policy."
        res.append({
            "id": str(a.id),
            "complaint_id": str(a.complaint_id),
            "complaint_number": c.complaint_number if c else "Unknown",
            "action_type": a.action_type,
            "remarks": remarks,
            "bureau": a.bureau.bureau_name if a.bureau else None,
            "officer": a.officer.full_name if (a.officer and has_access) else "Authorized Officer",
            "timestamp": str(a.timestamp) if a.timestamp else None,
            "previous_status": a.previous_status.value if a.previous_status else None,
            "new_status": a.new_status.value if a.new_status else None,
        })
    return res
