"""Shared fixtures/helpers used by the integration tests."""
import os
from datetime import date, timedelta
from typing import Optional

from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.main import app
from app.models import Bureau, Institution, User, UserRole

PASSWORD = "DemoPass123!"
PASSWORD_HASH = get_password_hash(PASSWORD)

SEED = {}


def seed_database():
    db = SessionLocal()
    try:
        bureaus = [
            Bureau(
                bureau_code="REG",
                bureau_name="Regulation Bureau",
                description="Regulatory complaints",
            ),
            Bureau(
                bureau_code="PGRC",
                bureau_name="Public Grievance Redressal Cell",
                description="Public grievances",
            ),
        ]
        db.add_all(bureaus)
        db.flush()

        users = [
            User(
                full_name="Test Super Admin",
                email="admin@test.demo",
                password_hash=PASSWORD_HASH,
                role=UserRole.SUPER_ADMIN,
                active=True,
            ),
            User(
                full_name="Test Bureau Admin",
                email="bureauadmin@test.demo",
                password_hash=PASSWORD_HASH,
                role=UserRole.BUREAU_ADMIN,
                bureau_id=bureaus[0].id,
                active=True,
            ),
            User(
                full_name="Test Case Officer",
                email="officer@test.demo",
                password_hash=PASSWORD_HASH,
                role=UserRole.CASE_OFFICER,
                bureau_id=bureaus[0].id,
                active=True,
            ),
            User(
                full_name="Test Senior Management",
                email="management@test.demo",
                password_hash=PASSWORD_HASH,
                role=UserRole.SENIOR_MANAGEMENT,
                active=True,
            ),
            User(
                full_name="Test Regional Officer",
                email="regional@test.demo",
                password_hash=PASSWORD_HASH,
                role=UserRole.REGIONAL_OFFICER,
                bureau_id=bureaus[1].id,
                active=True,
            ),
        ]
        db.add_all(users)
        db.flush()

        institution = Institution(
            institution_name="Test Institute of Technology",
            normalized_name="test institute of technology",
            aicte_permanent_id="AICTE-TEST-001",
            institution_type="Engineering",
            city="Pune",
            state="Maharashtra",
            region="West",
            contact_email="office@test.edu.in",
            institution_status="Active",
        )
        db.add(institution)
        db.commit()

        SEED.clear()
        SEED.update(
            {
                "bureaus": [str(b.id) for b in bureaus],
                "bureau_names": [b.bureau_name for b in bureaus],
                "users": [str(u.id) for u in users],
                "institution": str(institution.id),
                "institution_name": institution.institution_name,
            }
        )
    finally:
        db.close()


def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()


def make_client() -> TestClient:
    return TestClient(app)


def login(client: TestClient, email: str = "admin@test.demo", password: str = PASSWORD) -> str:
    response = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_institution(client: TestClient, token: str, name: str = "Workflow Institute") -> dict:
    response = client.post(
        "/api/institutions",
        headers=auth(token),
        json={
            "institution_name": name,
            "institution_type": "Engineering",
            "region": "West",
            "state": "Maharashtra",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_complaint(
    client: TestClient,
    token: str,
    institution_id: Optional[str] = None,
    bureau_id: Optional[str] = None,
    officer_id: Optional[str] = None,
    subject: str = "Laboratory equipment is not working",
    description: str = "Laboratory equipment has been broken for weeks and practical classes cannot run.",
    category: str = "Infrastructure",
    priority: str = "High",
) -> dict:
    today = date.today()
    response = client.post(
        "/api/complaints",
        headers=auth(token),
        json={
            "institution_id": institution_id or SEED["institution"],
            "received_date": today.isoformat(),
            "source_channel": "Online Portal",
            "category": category,
            "subject": subject,
            "description": description,
            "priority": priority,
            "assigned_bureau_id": bureau_id or SEED["bureaus"][0],
            "assigned_officer_id": officer_id or SEED["users"][2],
            "expected_disposal_date": (today + timedelta(days=30)).isoformat(),
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
