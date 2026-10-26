from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import parse_uuid, require_super_admin
from app.models.bureau import Bureau
from app.models.complaint import Complaint
from app.models.user import User
from app.utils.helpers import record_audit

router = APIRouter()


class BureauCreate(BaseModel):
    bureau_code: str = Field(min_length=2, max_length=20)
    bureau_name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)


class BureauUpdate(BaseModel):
    bureau_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)
    active: Optional[bool] = None


def serialize_bureau(bureau: Bureau, complaint_count: int = 0, user_count: int = 0) -> dict:
    return {
        "id": str(bureau.id),
        "bureau_code": bureau.bureau_code,
        "bureau_name": bureau.bureau_name,
        "description": bureau.description,
        "active": bureau.active,
        "complaint_count": complaint_count,
        "user_count": user_count,
    }


@router.get("")
def list_bureaus(db: Session = Depends(get_db)):
    bureaus = db.query(Bureau).order_by(Bureau.bureau_name.asc()).all()
    ids = [b.id for b in bureaus]
    complaint_counts = {}
    user_counts = {}
    if ids:
        complaint_counts = dict(
            db.query(Complaint.assigned_bureau_id, func.count(Complaint.id))
            .filter(Complaint.assigned_bureau_id.in_(ids))
            .group_by(Complaint.assigned_bureau_id)
            .all()
        )
        user_counts = dict(
            db.query(User.bureau_id, func.count(User.id))
            .filter(User.bureau_id.in_(ids))
            .group_by(User.bureau_id)
            .all()
        )
    return [
        serialize_bureau(b, complaint_counts.get(b.id, 0), user_counts.get(b.id, 0))
        for b in bureaus
    ]


@router.post("", status_code=201)
def create_bureau(
    payload: BureauCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    code = payload.bureau_code.strip().upper()
    if db.query(Bureau).filter(Bureau.bureau_code == code).first():
        raise HTTPException(status_code=409, detail="A bureau with this code already exists")

    bureau = Bureau(
        bureau_code=code,
        bureau_name=payload.bureau_name.strip(),
        description=(payload.description or "").strip() or None,
        active=True,
    )
    db.add(bureau)
    try:
        db.flush()
        record_audit(db, current_user, "CREATE", "Bureau", bureau.id, {"code": code})
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bureau could not be created")
    db.refresh(bureau)
    return {"message": "Bureau created successfully", **serialize_bureau(bureau)}


@router.patch("/{id}")
def update_bureau(
    id: str,
    payload: BureauUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    bureau = db.query(Bureau).filter(Bureau.id == parse_uuid(id)).first()
    if not bureau:
        raise HTTPException(status_code=404, detail="Bureau not found")

    changes = payload.dict(exclude_unset=True)
    for key, value in changes.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(bureau, key, value)
    record_audit(db, current_user, "UPDATE", "Bureau", bureau.id, changes)
    db.commit()
    db.refresh(bureau)
    return {"message": "Bureau updated successfully", **serialize_bureau(bureau)}
