"""Shared FastAPI dependencies: authentication, authorisation, ABAC, and ID parsing."""
import uuid
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False
)

# Roles that may create/change records. Senior management & auditor are read-only by default.
WRITE_ROLES = (
    UserRole.SUPER_ADMIN,
    UserRole.ADMIN,
    UserRole.BUREAU_ADMIN,
    UserRole.CASE_OFFICER,
    UserRole.RB_OFFICER,
    UserRole.PGRC_OFFICER,
    UserRole.REGIONAL_OFFICER,
)

ADMIN_ROLES = (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.BUREAU_ADMIN)


def parse_uuid(value: str, field: str = "id") -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field}",
        )


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_error
        user_uuid = uuid.UUID(str(user_id))
    except (JWTError, ValueError):
        raise credentials_error

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            return None
        user_uuid = uuid.UUID(str(user_id))
    except (JWTError, ValueError):
        return None

    return db.query(User).filter(User.id == user_uuid, User.active == True).first()


def require_roles(*roles):
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' does not have permission for this action",
            )
        return current_user

    return _checker


require_writer = require_roles(*WRITE_ROLES)
require_admin = require_roles(*ADMIN_ROLES)
require_super_admin = require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)
require_auditor = require_roles(UserRole.AUDITOR, UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.BUREAU_ADMIN)
