from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User
from app.utils.helpers import record_audit

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str


class UserMe(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    bureau_id: Optional[str] = None
    bureau_code: Optional[str] = None
    bureau_name: Optional[str] = None
    region_permissions: Optional[str] = None
    active: bool
    mfa_enabled: bool = False


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class MfaToggle(BaseModel):
    mfa_enabled: bool


def serialize_me(user: User) -> dict:
    return {
        "id": str(user.id),
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "bureau_id": str(user.bureau_id) if user.bureau_id else None,
        "bureau_code": user.bureau.bureau_code if user.bureau else None,
        "bureau_name": user.bureau.bureau_name if user.bureau else None,
        "region_permissions": user.region_permissions or "All",
        "active": user.active,
        "mfa_enabled": bool(user.mfa_enabled),
    }


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username.strip().lower()).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.active:
        raise HTTPException(status_code=400, detail="This account has been deactivated")

    user.last_login_at = datetime.utcnow()
    record_audit(db, user, "LOGIN", "User", user.id, {"email": user.email, "role": user.role.value})
    db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "full_name": user.full_name,
    }


@router.post("/refresh", response_model=Token)
def refresh_token(current_user: User = Depends(get_current_user)):
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=current_user.id, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        "full_name": current_user.full_name,
    }


@router.get("/me", response_model=UserMe)
def me(current_user: User = Depends(get_current_user)):
    return serialize_me(current_user)


@router.post("/change-password")
def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password does not match")
    current_user.password_hash = get_password_hash(payload.new_password)
    record_audit(db, current_user, "PASSWORD_CHANGE", "User", current_user.id)
    db.commit()
    return {"message": "Password updated successfully"}


@router.post("/mfa/toggle")
def toggle_mfa(
    payload: MfaToggle,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Toggle TOTP MFA for demo compliance."""
    current_user.mfa_enabled = payload.mfa_enabled
    record_audit(db, current_user, "MFA_TOGGLE", "User", current_user.id, {"mfa_enabled": payload.mfa_enabled})
    db.commit()
    return {"message": f"MFA {'enabled' if payload.mfa_enabled else 'disabled'}", "mfa_enabled": current_user.mfa_enabled}
