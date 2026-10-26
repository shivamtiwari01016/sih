from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import parse_uuid, require_writer
from app.models.bureau import Bureau
from app.models.bureau_transfer import BureauTransfer, TransferStatus
from app.models.case_action import CaseAction
from app.models.complaint import Complaint, ComplaintStatus
from app.models.user import User
from app.utils.helpers import notify, record_audit

router = APIRouter()


class CoordinationCreate(BaseModel):
    complaint_id: str
    to_bureau_id: str
    reason: str = Field(min_length=3, max_length=2000)


class CommentCreate(BaseModel):
    comment: str = Field(min_length=1, max_length=2000)


def serialize_coordination(transfer: BureauTransfer) -> dict:
    complaint = transfer.complaint
    return {
        "id": str(transfer.id),
        "complaint_id": str(transfer.complaint_id),
        "complaint_number": complaint.complaint_number if complaint else None,
        "complaint_subject": complaint.subject if complaint else None,
        "complaint_status": (
            complaint.current_status.value if complaint and complaint.current_status else None
        ),
        "institution": (
            complaint.institution.institution_name
            if complaint and complaint.institution
            else None
        ),
        "from_bureau": transfer.from_bureau.bureau_name if transfer.from_bureau else None,
        "from_bureau_id": str(transfer.from_bureau_id),
        "to_bureau": transfer.to_bureau.bureau_name if transfer.to_bureau else None,
        "to_bureau_id": str(transfer.to_bureau_id),
        "reason": transfer.reason,
        "status": transfer.transfer_status.value if transfer.transfer_status else None,
        "requested_by": transfer.requester.full_name if transfer.requester else None,
        "approved_by": transfer.approver.full_name if transfer.approver else None,
        "created_at": str(transfer.created_at) if transfer.created_at else None,
        "completed_at": str(transfer.completed_at) if transfer.completed_at else None,
    }


@router.get("")
def list_coordination(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = db.query(BureauTransfer)
    if status:
        matched = None
        for transfer_status in TransferStatus:
            if status.strip().lower() in (
                transfer_status.value.lower(),
                transfer_status.name.lower(),
            ):
                matched = transfer_status
                break
        if not matched:
            raise HTTPException(status_code=400, detail="Invalid coordination status")
        query = query.filter(BureauTransfer.transfer_status == matched)

    transfers = (
        query.order_by(BureauTransfer.created_at.desc()).offset(skip).limit(limit).all()
    )
    return [serialize_coordination(t) for t in transfers]


@router.post("", status_code=201)
def create_coordination(
    payload: CoordinationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == parse_uuid(payload.complaint_id, "complaint id"))
        .first()
    )
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
            detail="Assign the complaint to a bureau before requesting coordination",
        )
    if from_uuid == to_uuid:
        raise HTTPException(status_code=400, detail="Complaint already belongs to this bureau")

    transfer = BureauTransfer(
        complaint_id=complaint.id,
        from_bureau_id=from_uuid,
        to_bureau_id=to_uuid,
        requested_by=current_user.id,
        reason=payload.reason.strip(),
        transfer_status=TransferStatus.PENDING,
    )
    db.add(transfer)
    db.add(
        CaseAction(
            complaint_id=complaint.id,
            action_type="Coordination Request",
            previous_status=complaint.current_status,
            new_status=complaint.current_status,
            remarks=f"Coordination requested with {to_bureau.bureau_name}: {payload.reason.strip()}",
            officer_id=current_user.id,
            bureau_id=from_uuid,
        )
    )
    complaint.last_action_at = datetime.utcnow()

    recipients = (
        db.query(User)
        .filter(User.bureau_id == to_uuid, User.active.is_(True))
        .all()
    )
    for recipient in recipients:
        notify(
            db,
            recipient.id,
            "Coordination Request",
            "New cross-bureau coordination request",
            f"{complaint.complaint_number} requires coordination with your bureau.",
            "Warning",
            complaint.id,
        )

    record_audit(
        db,
        current_user,
        "CREATE_COORDINATION",
        "BureauTransfer",
        transfer.id,
        {"complaint": complaint.complaint_number, "to_bureau": to_bureau.bureau_name},
    )
    db.commit()
    db.refresh(transfer)
    return {
        "message": "Coordination request created",
        "coordination": serialize_coordination(transfer),
    }


@router.post("/{id}/acknowledge")
def acknowledge(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    transfer = db.query(BureauTransfer).filter(BureauTransfer.id == parse_uuid(id)).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Coordination request not found")
    if transfer.transfer_status != TransferStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only pending requests can be acknowledged")

    transfer.transfer_status = TransferStatus.APPROVED
    transfer.approved_by = current_user.id

    record_audit(
        db,
        current_user,
        "ACKNOWLEDGE_COORDINATION",
        "BureauTransfer",
        transfer.id,
    )
    db.commit()
    db.refresh(transfer)
    return {"message": "Coordination request acknowledged", "coordination": serialize_coordination(transfer)}


@router.post("/{id}/comments")
def add_comment(
    id: str,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    transfer = db.query(BureauTransfer).filter(BureauTransfer.id == parse_uuid(id)).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Coordination request not found")

    action = CaseAction(
        complaint_id=transfer.complaint_id,
        action_type="Coordination Comment",
        previous_status=transfer.complaint.current_status if transfer.complaint else None,
        new_status=transfer.complaint.current_status if transfer.complaint else None,
        remarks=payload.comment.strip(),
        officer_id=current_user.id,
        bureau_id=current_user.bureau_id or transfer.from_bureau_id,
    )
    db.add(action)
    record_audit(
        db,
        current_user,
        "COORDINATION_COMMENT",
        "BureauTransfer",
        transfer.id,
        {"comment": payload.comment},
    )
    db.commit()
    return {"message": "Comment added", "comment": payload.comment.strip()}


@router.post("/{id}/resolve")
def resolve(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_writer),
):
    transfer = db.query(BureauTransfer).filter(BureauTransfer.id == parse_uuid(id)).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Coordination request not found")
    if transfer.transfer_status == TransferStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Coordination request is already completed")

    complaint = transfer.complaint
    if complaint:
        complaint.assigned_bureau_id = transfer.to_bureau_id
        if complaint.current_status in (ComplaintStatus.RECEIVED, ComplaintStatus.UNDER_SCRUTINY):
            complaint.current_status = ComplaintStatus.UNDER_PROCESS
        complaint.last_action_at = datetime.utcnow()
        db.add(
            CaseAction(
                complaint_id=complaint.id,
                action_type="Coordination Resolved",
                previous_status=complaint.current_status,
                new_status=complaint.current_status,
                remarks=f"Case transferred to {transfer.to_bureau.bureau_name if transfer.to_bureau else 'destination bureau'} through coordination.",
                officer_id=current_user.id,
                bureau_id=transfer.to_bureau_id,
            )
        )

    transfer.transfer_status = TransferStatus.COMPLETED
    transfer.completed_at = datetime.utcnow()
    if not transfer.approved_by:
        transfer.approved_by = current_user.id

    if transfer.requested_by and transfer.requested_by != current_user.id:
        notify(
            db,
            transfer.requested_by,
            "Coordination Request",
            "Coordination request resolved",
            f"Coordination request {transfer.id} has been completed.",
            "Info",
            transfer.complaint_id,
        )

    record_audit(
        db,
        current_user,
        "RESOLVE_COORDINATION",
        "BureauTransfer",
        transfer.id,
    )
    db.commit()
    db.refresh(transfer)
    return {"message": "Coordination request resolved", "coordination": serialize_coordination(transfer)}
