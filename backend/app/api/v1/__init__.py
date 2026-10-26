from fastapi import APIRouter, Depends

from app.api.v1.endpoints import (
    auth,
    dashboard,
    institutions,
    complaints,
    overlaps,
    coordination,
    notifications,
    reports,
    users,
    bureaus,
    audit_logs,
)
from app.core.deps import get_current_user

api_router = APIRouter()

# Public authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Every other route requires a valid JWT.
protected = APIRouter(dependencies=[Depends(get_current_user)])
protected.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
protected.include_router(institutions.router, prefix="/institutions", tags=["Institutions"])
protected.include_router(complaints.router, prefix="/complaints", tags=["Complaints"])
protected.include_router(overlaps.router, prefix="/overlaps", tags=["Overlap Intelligence"])
protected.include_router(coordination.router, prefix="/coordination", tags=["Coordination"])
protected.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
protected.include_router(reports.router, prefix="/reports", tags=["Reports"])
protected.include_router(users.router, prefix="/users", tags=["Users"])
protected.include_router(bureaus.router, prefix="/bureaus", tags=["Bureaus"])
protected.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])

api_router.include_router(protected)
