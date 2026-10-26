from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import parse_uuid, require_super_admin
from app.core.security import get_password_hash
from app.models.bureau import Bureau
from app.models.user import User, UserRole
from app.utils.helpers import record_audit

router = APIRouter()


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: str
    bureau_id: Optional[str] = None
    region_permissions: Optional[str] = None
    active: bool = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    email: Optional[str] = Field(default=None, min_length=5, max_length=255)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    role: Optional[str] = None
    bureau_id: Optional[str] = None
    region_permissions: Optional[str] = None
    active: Optional[bool] = None


def parse_role(value: str) -> UserRole:
    if value is None:
        raise HTTPException(status_code=400, detail="Role is required")
    for role in UserRole:
        if value.strip().lower() in (role.value.lower(), role.name.lower()):
            return role
    raise HTTPException(
        status_code=400,
        detail=f"Invalid role. Allowed: {', '.join(r.value for r in UserRole)}",
    )


def serialize_user(user: User) -> dict:
    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "bureau_id": str(user.bureau_id) if user.bureau_id else None,
        "bureau_name": user.bureau.bureau_name if user.bureau else None,
        "region_permissions": user.region_permissions or "All",
        "active": user.active,
        "mfa_enabled": bool(user.mfa_enabled),
        "last_login_at": str(user.last_login_at) if user.last_login_at else None,
        "created_at": str(user.created_at) if user.created_at else None,
    }


@router.get("")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.full_name.asc()).all()
    return [serialize_user(u) for u in users]


@router.get("/officers")
def list_officers(db: Session = Depends(get_db)):
    users = (
        db.query(User)
        .filter(
            User.active.is_(True),
            User.role.in_(
                [
                    UserRole.CASE_OFFICER,
                    UserRole.BUREAU_ADMIN,
                    UserRole.REGIONAL_OFFICER,
                ]
            ),
        )
        .order_by(User.full_name.asc())
        .all()
    )
    return [serialize_user(u) for u in users]


@router.post("", status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    email = payload.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    role = parse_role(payload.role)
    bureau_uuid = None
    if payload.bureau_id:
        bureau_uuid = parse_uuid(payload.bureau_id, "bureau id")
        if not db.query(Bureau).filter(Bureau.id == bureau_uuid).first():
            raise HTTPException(status_code=404, detail="Bureau not found")
    if role in (UserRole.BUREAU_ADMIN, UserRole.CASE_OFFICER, UserRole.REGIONAL_OFFICER) and not bureau_uuid:
        raise HTTPException(status_code=400, detail="This role requires a bureau")

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=get_password_hash(payload.password),
        role=role,
        bureau_id=bureau_uuid,
        region_permissions=(payload.region_permissions or "").strip() or None,
        active=payload.active,
    )
    db.add(user)
    db.flush()
    record_audit(
        db,
        current_user,
        "CREATE",
        "User",
        user.id,
        {"email": email, "role": role.value},
    )
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully", **serialize_user(user)}


@router.patch("/{id}")
def update_user(
    id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    user = db.query(User).filter(User.id == parse_uuid(id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = payload.dict(exclude_unset=True)
    if "email" in changes and changes["email"]:
        email = changes["email"].strip().lower()
        duplicate = db.query(User).filter(User.email == email, User.id != user.id).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="A user with this email already exists")
        changes["email"] = email

    if "role" in changes and changes["role"]:
        user.role = parse_role(changes.pop("role"))

    if "bureau_id" in changes:
        bureau_id = changes.pop("bureau_id")
        if bureau_id:
            bureau_uuid = parse_uuid(bureau_id, "bureau id")
            if not db.query(Bureau).filter(Bureau.id == bureau_uuid).first():
                raise HTTPException(status_code=404, detail="Bureau not found")
            user.bureau_id = bureau_uuid
        else:
            user.bureau_id = None

    if "password" in changes and changes["password"]:
        user.password_hash = get_password_hash(changes.pop("password"))
    else:
        changes.pop("password", None)

    for key, value in changes.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(user, key, value)

    if user.role in (
        UserRole.BUREAU_ADMIN,
        UserRole.CASE_OFFICER,
        UserRole.REGIONAL_OFFICER,
    ) and not user.bureau_id:
        db.rollback()
        raise HTTPException(status_code=400, detail="This role requires a bureau")

    record_audit(db, current_user, "UPDATE", "User", user.id, {"active": user.active, "role": user.role.value})
    db.commit()
    db.refresh(user)
    return {"message": "User updated successfully", **serialize_user(user)}
