import csv
import io
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.bureau import Bureau
from app.models.complaint import Complaint, ComplaintStatus
from app.models.institution import Institution
from app.models.related_case import RelatedCase, ReviewStatus
from app.models.user import User

router = APIRouter()

OPEN_STATUSES = (
    ComplaintStatus.RECEIVED,
    ComplaintStatus.UNDER_SCRUTINY,
    ComplaintStatus.UNDER_PROCESS,
    ComplaintStatus.AWAITING_INFORMATION,
    ComplaintStatus.TRANSFERRED,
    ComplaintStatus.ESCALATED,
)


def _age_bucket(days: int) -> str:
    if days <= 7:
        return "0-7 days"
    if days <= 15:
        return "8-15 days"
    if days <= 30:
        return "16-30 days"
    if days <= 60:
        return "31-60 days"
    return "60+ days"


@router.get("/summary")
def report_summary(db: Session = Depends(get_db)):
    complaints = db.query(Complaint).all()
    total = len(complaints)
    status_counts = {status.value: 0 for status in ComplaintStatus}
    priority_counts = {}
    category_counts = {}

    for complaint in complaints:
        if complaint.current_status:
            status_counts[complaint.current_status.value] += 1
        priority = complaint.priority.value if complaint.priority else "Unspecified"
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
        category_counts[complaint.category] = category_counts.get(complaint.category, 0) + 1

    disposed = status_counts[ComplaintStatus.DISPOSED.value] + status_counts[
        ComplaintStatus.CLOSED.value
    ]
    overdue = sum(
        1
        for c in complaints
        if c.expected_disposal_date
        and c.expected_disposal_date < date.today()
        and c.current_status not in (ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED)
    )
    open_cases = [c for c in complaints if c.current_status in OPEN_STATUSES]
    avg_age = (
        round(
            sum((date.today() - c.received_date).days for c in open_cases) / len(open_cases),
            1,
        )
        if open_cases
        else 0
    )

    return {
        "total": total,
        "open": len(open_cases),
        "disposed": disposed,
        "overdue": overdue,
        "disposal_rate": round((disposed / total) * 100, 1) if total else 0,
        "average_open_age_days": avg_age,
        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "category_counts": category_counts,
        "institutions": db.query(func.count(Institution.id)).scalar() or 0,
        "overlap_suggestions": (
            db.query(func.count(RelatedCase.id))
            .filter(RelatedCase.review_status == ReviewStatus.SUGGESTED)
            .scalar()
            or 0
        ),
    }


@router.get("/ageing")
def report_ageing(db: Session = Depends(get_db)):
    buckets = {
        "0-7 days": 0,
        "8-15 days": 0,
        "16-30 days": 0,
        "31-60 days": 0,
        "60+ days": 0,
    }
    complaints = (
        db.query(Complaint)
        .filter(Complaint.current_status.in_(OPEN_STATUSES))
        .all()
    )
    for complaint in complaints:
        days = max((date.today() - complaint.received_date).days, 0)
        buckets[_age_bucket(days)] += 1

    return {
        "total_open": len(complaints),
        "buckets": [{"bucket": name, "count": count} for name, count in buckets.items()],
    }


def _last_months(count: int = 6):
    today = date.today()
    months = []
    year, month = today.year, today.month
    for _ in range(count):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(months))


@router.get("/disposal")
def report_disposal(db: Session = Depends(get_db)):
    months = _last_months(6)
    labels = [f"{year:04d}-{month:02d}" for year, month in months]
    received = {label: 0 for label in labels}
    disposed = {label: 0 for label in labels}

    for complaint in db.query(Complaint).all():
        if complaint.received_date:
            key = f"{complaint.received_date.year:04d}-{complaint.received_date.month:02d}"
            if key in received:
                received[key] += 1
        if complaint.disposed_at and complaint.current_status in (
            ComplaintStatus.DISPOSED,
            ComplaintStatus.CLOSED,
        ):
            disposed_date = (
                complaint.disposed_at.date()
                if isinstance(complaint.disposed_at, datetime)
                else complaint.disposed_at
            )
            key = f"{disposed_date.year:04d}-{disposed_date.month:02d}"
            if key in disposed:
                disposed[key] += 1

    return [
        {
            "month": label,
            "received": received[label],
            "disposed": disposed[label],
        }
        for label in labels
    ]


@router.get("/bureaus")
def report_bureaus(db: Session = Depends(get_db)):
    result = []
    for bureau in db.query(Bureau).order_by(Bureau.bureau_name.asc()).all():
        base = db.query(Complaint).filter(Complaint.assigned_bureau_id == bureau.id)
        total = base.count()
        disposed = base.filter(
            Complaint.current_status.in_([ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED])
        ).count()
        open_count = base.filter(Complaint.current_status.in_(OPEN_STATUSES)).count()
        overdue = (
            base.filter(
                Complaint.expected_disposal_date < date.today(),
                ~Complaint.current_status.in_(
                    [ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED]
                ),
            ).count()
        )
        result.append(
            {
                "bureau_id": str(bureau.id),
                "bureau_name": bureau.bureau_name,
                "bureau_code": bureau.bureau_code,
                "total": total,
                "open": open_count,
                "disposed": disposed,
                "overdue": overdue,
                "disposal_rate": round((disposed / total) * 100, 1) if total else 0,
            }
        )
    return result


@router.get("/export")
def export_report(
    search: Optional[str] = None,
    status: Optional[str] = None,
    bureau_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Complaint)
    if search:
        term = f"%{search.strip()}%"
        query = query.join(Institution, Complaint.institution_id == Institution.id).filter(
            (Complaint.complaint_number.ilike(term))
            | (Complaint.subject.ilike(term))
            | (Institution.institution_name.ilike(term))
        )
    if status:
        for allowed in ComplaintStatus:
            if status.strip().lower() in (allowed.value.lower(), allowed.name.lower()):
                query = query.filter(Complaint.current_status == allowed)
                break
    if bureau_id:
        query = query.filter(Complaint.assigned_bureau_id == bureau_id)

    complaints = query.order_by(Complaint.received_date.desc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Complaint Number",
            "Institution",
            "Category",
            "Subject",
            "Priority",
            "Status",
            "Assigned Bureau",
            "Assigned Officer",
            "Received Date",
            "Expected Disposal Date",
            "Disposed At",
            "Overdue",
        ]
    )
    for complaint in complaints:
        writer.writerow(
            [
                complaint.complaint_number,
                complaint.institution.institution_name if complaint.institution else "",
                complaint.category,
                complaint.subject,
                complaint.priority.value if complaint.priority else "",
                complaint.current_status.value if complaint.current_status else "",
                complaint.assigned_bureau.bureau_name if complaint.assigned_bureau else "",
                complaint.assigned_officer.full_name if complaint.assigned_officer else "",
                str(complaint.received_date),
                str(complaint.expected_disposal_date or ""),
                str(complaint.disposed_at or ""),
                "Yes"
                if complaint.expected_disposal_date
                and complaint.expected_disposal_date < date.today()
                and complaint.current_status
                not in (ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED)
                else "No",
            ]
        )

    filename = f"civicresolve-complaints-{date.today().isoformat()}.csv"
    response = StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
