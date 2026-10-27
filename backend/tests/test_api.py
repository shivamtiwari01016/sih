"""End-to-end API integration tests.

Run from the backend directory with: ``pytest tests/ -v``
"""
import uuid
from datetime import date, timedelta

from helpers import (
    PASSWORD,
    SEED,
    auth,
    create_complaint,
    create_institution,
    login,
)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_login_success_and_current_user(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "admin@samanvay.demo", "password": PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

    me = client.get("/api/auth/me", headers=auth(body["access_token"]))
    assert me.status_code == 200
    profile = me.json()
    assert profile["email"] == "admin@samanvay.demo"
    assert profile["role"] == "Super Administrator"
    assert profile["bureau_id"] is None
    assert profile["bureau_name"] is None
    assert profile["active"] is True


def test_login_rejects_bad_credentials(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "admin@samanvay.demo", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_protected_routes_require_authentication(client):
    assert client.get("/api/complaints").status_code == 401
    assert client.get("/api/dashboard/summary").status_code == 401
    assert client.get("/api/auth/me").status_code == 401


def test_change_password_flow(client):
    token = login(client)
    response = client.post(
        "/api/auth/change-password",
        headers=auth(token),
        json={"current_password": PASSWORD, "new_password": "NewPass123!"},
    )
    assert response.status_code == 200

    assert (
        client.post(
            "/api/auth/login",
            data={"username": "admin@samanvay.demo", "password": PASSWORD},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/auth/login",
            data={"username": "admin@samanvay.demo", "password": "NewPass123!"},
        ).status_code
        == 200
    )


# ---------------------------------------------------------------------------
# Institutions
# ---------------------------------------------------------------------------
def test_institution_registration_and_lookup(client):
    token = login(client)

    created = create_institution(client, token, "New Horizon Institute of Technology")
    assert created["institution_name"] == "New Horizon Institute of Technology"
    assert created["complaint_count"] == 0

    listing = client.get("/api/institutions", headers=auth(token))
    assert listing.status_code == 200
    names = [item["institution_name"] for item in listing.json()]
    assert "New Horizon Institute of Technology" in names

    search = client.get(
        "/api/institutions", headers=auth(token), params={"search": "Horizon"}
    )
    assert search.status_code == 200
    assert any("Horizon" in item["institution_name"] for item in search.json())

    detail = client.get(f"/api/institutions/{created['id']}", headers=auth(token))
    assert detail.status_code == 200
    assert detail.json()["aicte_permanent_id"] is None

    complaints = client.get(
        f"/api/institutions/{created['id']}/complaints", headers=auth(token)
    )
    assert complaints.status_code == 200
    assert complaints.json() == []


def test_institution_validation_and_duplicates(client):
    token = login(client)
    create_institution(client, token, "Duplicate Institute")

    duplicate = client.post(
        "/api/institutions",
        headers=auth(token),
        json={"institution_name": "duplicate institute"},
    )
    assert duplicate.status_code == 409

    short_name = client.post(
        "/api/institutions", headers=auth(token), json={"institution_name": "X"}
    )
    assert short_name.status_code == 422

    missing_name = client.post("/api/institutions", headers=auth(token), json={})
    assert missing_name.status_code == 422

    duplicate_aicte = client.post(
        "/api/institutions",
        headers=auth(token),
        json={"institution_name": "Another Institute", "aicte_permanent_id": "AICTE-TEST-001"},
    )
    assert duplicate_aicte.status_code == 409


def test_institution_update(client):
    token = login(client)
    created = create_institution(client, token, "Editable Institute")

    updated = client.patch(
        f"/api/institutions/{created['id']}",
        headers=auth(token),
        json={"city": "Mumbai", "contact_email": "contact@editable.edu.in"},
    )
    assert updated.status_code == 200
    assert updated.json()["city"] == "Mumbai"
    assert updated.json()["contact_email"] == "contact@editable.edu.in"

    renamed = client.patch(
        f"/api/institutions/{created['id']}",
        headers=auth(token),
        json={"institution_name": "Renamed Institute"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["institution_name"] == "Renamed Institute"

    conflicting = client.patch(
        f"/api/institutions/{created['id']}",
        headers=auth(token),
        json={"institution_name": SEED["institution_name"]},
    )
    assert conflicting.status_code == 409


def test_institution_not_found_and_invalid_id(client):
    token = login(client)
    assert (
        client.get(f"/api/institutions/{uuid.uuid4()}", headers=auth(token)).status_code
        == 404
    )
    assert (
        client.get("/api/institutions/not-a-uuid", headers=auth(token)).status_code == 400
    )


# ---------------------------------------------------------------------------
# Complaint registration and retrieval
# ---------------------------------------------------------------------------
def test_complaint_registration(client):
    token = login(client)
    complaint = create_complaint(client, token)

    assert complaint["complaint_number"].startswith(f"CR-{date.today().year}-")
    assert complaint["current_status"] == "Received"
    assert complaint["priority"] == "High"
    assert complaint["institution_name"] == SEED["institution_name"]
    assert complaint["assigned_bureau"] == "Regulation Bureau"
    assert complaint["assigned_officer"] == "Test Case Officer"
    assert complaint["is_overdue"] is False
    assert complaint["message"] == "Complaint registered successfully"

    detail = client.get(f"/api/complaints/{complaint['id']}", headers=auth(token))
    assert detail.status_code == 200
    body = detail.json()
    assert body["institution"]["name"] == SEED["institution_name"]
    assert len(body["actions"]) == 1
    assert body["actions"][0]["action_type"] == "Registration"
    assert body["transfers"] == []

    institution_complaints = client.get(
        f"/api/institutions/{SEED['institution']}/complaints", headers=auth(token)
    )
    assert institution_complaints.status_code == 200
    assert len(institution_complaints.json()) == 1


def test_complaint_validation_rules(client):
    token = login(client)

    missing_institution = client.post(
        "/api/complaints",
        headers=auth(token),
        json={
            "institution_id": str(uuid.uuid4()),
            "category": "Infrastructure",
            "subject": "Valid subject",
            "description": "Valid description for the complaint",
        },
    )
    assert missing_institution.status_code == 404

    invalid_institution = client.post(
        "/api/complaints",
        headers=auth(token),
        json={
            "institution_id": "not-a-uuid",
            "category": "Infrastructure",
            "subject": "Valid subject",
            "description": "Valid description for the complaint",
        },
    )
    assert invalid_institution.status_code == 400

    invalid_priority = client.post(
        "/api/complaints",
        headers=auth(token),
        json={
            "institution_id": SEED["institution"],
            "category": "Infrastructure",
            "subject": "Valid subject",
            "description": "Valid description for the complaint",
            "priority": "Extreme",
        },
    )
    assert invalid_priority.status_code == 400

    future_date = client.post(
        "/api/complaints",
        headers=auth(token),
        json={
            "institution_id": SEED["institution"],
            "category": "Infrastructure",
            "subject": "Future complaint",
            "description": "This complaint is received in the future.",
            "received_date": (date.today() + timedelta(days=10)).isoformat(),
        },
    )
    assert future_date.status_code == 400

    short_subject = client.post(
        "/api/complaints",
        headers=auth(token),
        json={
            "institution_id": SEED["institution"],
            "category": "Infrastructure",
            "subject": "X",
            "description": "Valid description for the complaint",
        },
    )
    assert short_subject.status_code == 422


def test_complaint_filters_and_search(client):
    token = login(client)
    first = create_complaint(client, token, subject="Fee refund request", category="Fee Structure")
    create_complaint(client, token, subject="Hostel infrastructure issue", category="Infrastructure")

    by_status = client.get(
        "/api/complaints", headers=auth(token), params={"status": "Received"}
    )
    assert by_status.status_code == 200
    assert len(by_status.json()) == 2

    by_priority = client.get(
        "/api/complaints", headers=auth(token), params={"priority": "High"}
    )
    assert by_priority.status_code == 200
    assert len(by_priority.json()) == 2

    by_category = client.get(
        "/api/complaints", headers=auth(token), params={"search": "Fee Structure"}
    )
    assert by_category.status_code == 200
    assert [c["subject"] for c in by_category.json()] == ["Fee refund request"]

    by_number = client.get(
        "/api/complaints",
        headers=auth(token),
        params={"search": first["complaint_number"]},
    )
    assert by_number.status_code == 200
    assert len(by_number.json()) == 1

    by_institution = client.get(
        "/api/complaints",
        headers=auth(token),
        params={"institution_id": SEED["institution"]},
    )
    assert by_institution.status_code == 200
    assert len(by_institution.json()) == 2

    by_bureau = client.get(
        "/api/complaints",
        headers=auth(token),
        params={"bureau_id": SEED["bureaus"][0]},
    )
    assert by_bureau.status_code == 200
    assert len(by_bureau.json()) == 2


# ---------------------------------------------------------------------------
# Complaint workflow
# ---------------------------------------------------------------------------
def test_assignment_status_and_disposal_workflow(client):
    token = login(client)
    complaint = create_complaint(client, token)

    assigned = client.post(
        f"/api/complaints/{complaint['id']}/assign",
        headers=auth(token),
        json={
            "bureau_id": SEED["bureaus"][1],
            "officer_id": SEED["users"][4],
            "remarks": "Regional office should handle this",
        },
    )
    assert assigned.status_code == 200
    assert assigned.json()["assigned_bureau"] == "Public Grievance Redressal Cell"
    assert assigned.json()["current_status"] == "Under Process"

    action = client.post(
        f"/api/complaints/{complaint['id']}/actions",
        headers=auth(token),
        json={
            "action_type": "Information Requested",
            "remarks": "Requested equipment repair records from the institution.",
            "new_status": "Awaiting Information",
            "next_action": "Follow up with institution",
        },
    )
    assert action.status_code == 200
    assert action.json()["complaint"]["current_status"] == "Awaiting Information"
    assert action.json()["action"]["action_type"] == "Information Requested"

    escalated = client.post(
        f"/api/complaints/{complaint['id']}/escalate",
        headers=auth(token),
        json={"reason": "Institution has not responded within the deadline"},
    )
    assert escalated.status_code == 200
    assert escalated.json()["current_status"] == "Escalated"

    disposed = client.post(
        f"/api/complaints/{complaint['id']}/dispose",
        headers=auth(token),
        json={"remarks": "Equipment was repaired and verified.", "disposal_outcome": "Resolved"},
    )
    assert disposed.status_code == 200
    assert disposed.json()["current_status"] == "Disposed"
    assert disposed.json()["disposed_at"]

    repeat = client.post(
        f"/api/complaints/{complaint['id']}/dispose",
        headers=auth(token),
        json={"remarks": "Trying to dispose twice"},
    )
    assert repeat.status_code == 400

    detail = client.get(f"/api/complaints/{complaint['id']}", headers=auth(token))
    action_types = [a["action_type"] for a in detail.json()["actions"]]
    assert "Registration" in action_types
    assert "Assignment" in action_types
    assert "Escalation" in action_types
    assert "Disposal" in action_types


def test_transfer_request_workflow(client):
    token = login(client)
    complaint = create_complaint(client, token)

    same_bureau = client.post(
        f"/api/complaints/{complaint['id']}/transfer",
        headers=auth(token),
        json={"to_bureau_id": SEED["bureaus"][0], "reason": "Same bureau test"},
    )
    assert same_bureau.status_code == 400

    transfer = client.post(
        f"/api/complaints/{complaint['id']}/transfer",
        headers=auth(token),
        json={
            "to_bureau_id": SEED["bureaus"][1],
            "reason": "The matter falls under the grievance cell",
        },
    )
    assert transfer.status_code == 200
    assert transfer.json()["transfer"]["status"] == "Pending"
    assert transfer.json()["transfer"]["to_bureau"] == "Public Grievance Redressal Cell"

    detail = client.get(f"/api/complaints/{complaint['id']}", headers=auth(token))
    assert len(detail.json()["transfers"]) == 1

    bad_target = client.post(
        f"/api/complaints/{complaint['id']}/transfer",
        headers=auth(token),
        json={"to_bureau_id": str(uuid.uuid4()), "reason": "Unknown target"},
    )
    assert bad_target.status_code == 404


def test_institution_full_detail_fields(client):
    token = login(client)
    response = client.post(
        "/api/institutions",
        headers=auth(token),
        json={
            "institution_name": "Detail Institute of Technology",
            "institution_type": "Engineering",
            "region": "West",
            "state": "Maharashtra",
            "city": "Pune",
            "district": "Pune",
            "website": "https://detail.example.edu.in",
            "established_year": 1994,
            "ownership": "Private",
            "affiliation": "Savitribai Phule Pune University",
        },
    )
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["website"] == "https://detail.example.edu.in"
    assert created["established_year"] == 1994
    assert created["ownership"] == "Private"
    assert created["affiliation"] == "Savitribai Phule Pune University"

    detail = client.get(f"/api/institutions/{created['id']}", headers=auth(token))
    assert detail.status_code == 200
    assert detail.json()["established_year"] == 1994


def test_overlap_scan_is_idempotent(client):
    token = login(client)
    first = create_complaint(client, token)
    second = create_complaint(client, token)
    assert second["overlap_suggestions"] >= 1
    assert second["matches"][0]["complaint_number"] == first["complaint_number"]

    scan = client.post("/api/overlaps/scan", headers=auth(token))
    assert scan.status_code == 200, scan.text
    assert scan.json()["matches_found"] == 0
    assert len(client.get("/api/overlaps", headers=auth(token)).json()) == 1


def test_overlap_matching_and_review(client):
    token = login(client)
    first = create_complaint(client, token)
    second = create_complaint(
        client,
        token,
        bureau_id=SEED["bureaus"][1],
        officer_id=SEED["users"][4],
    )

    # Registration runs matching automatically, so the suggestion exists
    # before any manual matching request.
    assert second["overlap_suggestions"] >= 1
    match = second["matches"][0]
    assert match["complaint_number"] == first["complaint_number"]
    assert match["similarity_score"] >= 0.55
    assert any("institution" in reason.lower() for reason in match["matching_reasons"])

    # Running matching again must not create duplicate suggestions.
    matching = client.post(
        f"/api/complaints/{second['id']}/run-matching", headers=auth(token)
    )
    assert matching.status_code == 200
    assert matching.json()["matches_found"] == 0

    again = client.post(
        f"/api/complaints/{second['id']}/run-matching", headers=auth(token)
    )
    assert again.status_code == 200
    assert again.json()["matches_found"] == 0

    overlaps = client.get("/api/overlaps", headers=auth(token))
    assert overlaps.status_code == 200
    suggestions = overlaps.json()
    assert len(suggestions) == 1
    suggestion = suggestions[0]
    assert suggestion["review_status"] == "Suggested"
    assert suggestion["complaint_1_institution"] == SEED["institution_name"]

    stats = client.get("/api/overlaps/stats", headers=auth(token))
    assert stats.status_code == 200
    assert stats.json()["total"] == 1
    assert stats.json()["Suggested"] == 1

    confirmed = client.post(
        f"/api/overlaps/{suggestion['id']}/confirm",
        headers=auth(token),
        json={"remarks": "Same laboratory issue reported twice."},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["overlap"]["review_status"] == "Confirmed Related"
    assert confirmed.json()["overlap"]["review_remarks"] == "Same laboratory issue reported twice."

    detail = client.get(f"/api/complaints/{first['id']}", headers=auth(token))
    assert len(detail.json()["related_cases"]) == 1
    assert detail.json()["related_cases"][0]["review_status"] == "Confirmed Related"


def test_overlap_reject_and_request_review(client):
    token = login(client)
    create_complaint(client, token)
    second = create_complaint(client, token)
    client.post(f"/api/complaints/{second['id']}/run-matching", headers=auth(token))
    suggestion = client.get("/api/overlaps", headers=auth(token)).json()[0]

    requested = client.post(
        f"/api/overlaps/{suggestion['id']}/request-review",
        headers=auth(token),
        json={"remarks": "Needs senior review"},
    )
    assert requested.status_code == 200
    assert requested.json()["overlap"]["review_status"] == "Requires Further Review"

    rejected = client.post(
        f"/api/overlaps/{suggestion['id']}/reject",
        headers=auth(token),
        json={"remarks": "Different matters"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["overlap"]["review_status"] == "Rejected"


# ---------------------------------------------------------------------------
# Coordination
# ---------------------------------------------------------------------------
def test_coordination_workflow(client):
    token = login(client)
    complaint = create_complaint(client, token)

    created = client.post(
        "/api/coordination",
        headers=auth(token),
        json={
            "complaint_id": complaint["id"],
            "to_bureau_id": SEED["bureaus"][1],
            "reason": "Joint review required for this institution",
        },
    )
    assert created.status_code == 201
    coordination = created.json()["coordination"]
    assert coordination["status"] == "Pending"
    assert coordination["from_bureau"] == "Regulation Bureau"
    assert coordination["to_bureau"] == "Public Grievance Redressal Cell"

    listing = client.get("/api/coordination", headers=auth(token))
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    acknowledged = client.post(
        f"/api/coordination/{coordination['id']}/acknowledge", headers=auth(token)
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["coordination"]["status"] == "Approved"

    comment = client.post(
        f"/api/coordination/{coordination['id']}/comments",
        headers=auth(token),
        json={"comment": "Reviewed the case file."},
    )
    assert comment.status_code == 200

    resolved = client.post(
        f"/api/coordination/{coordination['id']}/resolve", headers=auth(token)
    )
    assert resolved.status_code == 200
    assert resolved.json()["coordination"]["status"] == "Completed"

    detail = client.get(f"/api/complaints/{complaint['id']}", headers=auth(token))
    assert detail.json()["assigned_bureau"] == "Public Grievance Redressal Cell"

    pending_filter = client.get(
        "/api/coordination", headers=auth(token), params={"status": "Pending"}
    )
    assert pending_filter.status_code == 200
    assert pending_filter.json() == []


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
def test_notifications_are_created_and_can_be_read(client):
    admin_token = login(client)
    complaint = create_complaint(client, admin_token)

    officer_token = login(client, "officer@samanvay.demo")
    notifications = client.get("/api/notifications", headers=auth(officer_token))
    assert notifications.status_code == 200
    items = notifications.json()
    assert len(items) >= 1
    assert items[0]["complaint_id"] == complaint["id"]
    assert items[0]["read"] is False

    unread = client.get("/api/notifications/unread-count", headers=auth(officer_token))
    assert unread.status_code == 200
    assert unread.json()["unread"] >= 1

    marked = client.post(
        f"/api/notifications/{items[0]['id']}/read", headers=auth(officer_token)
    )
    assert marked.status_code == 200
    assert marked.json()["notification"]["read"] is True

    read_all = client.post("/api/notifications/read-all", headers=auth(officer_token))
    assert read_all.status_code == 200

    after = client.get(
        "/api/notifications", headers=auth(officer_token), params={"unread_only": True}
    )
    assert after.status_code == 200
    assert after.json() == []


# ---------------------------------------------------------------------------
# Dashboard & reports
# ---------------------------------------------------------------------------
def test_dashboard_endpoints(client):
    token = login(client)
    create_complaint(client, token)

    summary = client.get("/api/dashboard/summary", headers=auth(token))
    assert summary.status_code == 200
    data = summary.json()
    assert data["total_complaints"] == 1
    assert data["total_institutions"] >= 1
    assert "disposal_rate" in data

    trends = client.get("/api/dashboard/trends", headers=auth(token))
    assert trends.status_code == 200
    assert len(trends.json()) == 6
    assert trends.json()[-1]["received"] == 1

    workload = client.get("/api/dashboard/bureau-workload", headers=auth(token))
    assert workload.status_code == 200
    assert len(workload.json()) == 2
    regulation = [b for b in workload.json() if b["bureau_code"] == "REG"][0]
    assert regulation["total"] == 1
    assert regulation["open"] == 1

    priority = client.get("/api/dashboard/priority-actions", headers=auth(token))
    assert priority.status_code == 200
    assert set(priority.json()) == {
        "overdue_cases",
        "unreviewed_overlaps",
        "pending_coordination",
    }


def test_reports_endpoints_and_csv_export(client):
    token = login(client)
    complaint = create_complaint(client, token)

    summary = client.get("/api/reports/summary", headers=auth(token))
    assert summary.status_code == 200
    data = summary.json()
    assert data["total"] == 1
    assert data["open"] == 1
    assert data["priority_counts"]["High"] == 1
    assert data["category_counts"]["Infrastructure"] == 1

    ageing = client.get("/api/reports/ageing", headers=auth(token))
    assert ageing.status_code == 200
    assert ageing.json()["total_open"] == 1
    assert len(ageing.json()["buckets"]) == 5

    disposal = client.get("/api/reports/disposal", headers=auth(token))
    assert disposal.status_code == 200
    assert len(disposal.json()) == 6

    bureaus = client.get("/api/reports/bureaus", headers=auth(token))
    assert bureaus.status_code == 200
    assert len(bureaus.json()) == 2

    export = client.get("/api/reports/export", headers=auth(token))
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    assert "attachment;" in export.headers["content-disposition"]
    lines = export.text.splitlines()
    assert lines[0].startswith("Complaint Number")
    assert complaint["complaint_number"] in export.text

    filtered = client.get(
        "/api/reports/export",
        headers=auth(token),
        params={"search": complaint["complaint_number"]},
    )
    assert filtered.status_code == 200
    assert complaint["complaint_number"] in filtered.text


# ---------------------------------------------------------------------------
# Administration
# ---------------------------------------------------------------------------
def test_bureau_management(client):
    token = login(client)

    created = client.post(
        "/api/bureaus",
        headers=auth(token),
        json={
            "bureau_code": "EAP",
            "bureau_name": "Approval Process Bureau",
            "description": "Approval related matters",
        },
    )
    assert created.status_code == 201
    assert created.json()["bureau_code"] == "EAP"

    duplicate = client.post(
        "/api/bureaus",
        headers=auth(token),
        json={"bureau_code": "eap", "bureau_name": "Duplicate Code"},
    )
    assert duplicate.status_code == 409

    listing = client.get("/api/bureaus", headers=auth(token))
    assert listing.status_code == 200
    assert len(listing.json()) == 3

    updated = client.patch(
        f"/api/bureaus/{created.json()['id']}",
        headers=auth(token),
        json={"bureau_name": "Approvals Bureau", "active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["bureau_name"] == "Approvals Bureau"
    assert updated.json()["active"] is False


def test_user_management(client):
    token = login(client)

    missing_bureau = client.post(
        "/api/users",
        headers=auth(token),
        json={
            "full_name": "New Officer",
            "email": "newofficer@samanvay.demo",
            "password": "OfficerPass123!",
            "role": "Case Officer",
        },
    )
    assert missing_bureau.status_code == 400

    invalid_role = client.post(
        "/api/users",
        headers=auth(token),
        json={
            "full_name": "New User",
            "email": "newuser@samanvay.demo",
            "password": "UserPass123!",
            "role": "Wizard",
        },
    )
    assert invalid_role.status_code == 400

    created = client.post(
        "/api/users",
        headers=auth(token),
        json={
            "full_name": "New Officer",
            "email": "newofficer@samanvay.demo",
            "password": "OfficerPass123!",
            "role": "Case Officer",
            "bureau_id": SEED["bureaus"][0],
        },
    )
    assert created.status_code == 201
    assert created.json()["role"] == "Case Officer"
    assert created.json()["bureau_name"] == "Regulation Bureau"

    duplicate = client.post(
        "/api/users",
        headers=auth(token),
        json={
            "full_name": "Duplicate Officer",
            "email": "newofficer@samanvay.demo",
            "password": "OfficerPass123!",
            "role": "Case Officer",
            "bureau_id": SEED["bureaus"][0],
        },
    )
    assert duplicate.status_code == 409

    updated = client.patch(
        f"/api/users/{created.json()['id']}",
        headers=auth(token),
        json={"role": "Bureau Administrator", "active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "Bureau Administrator"
    assert updated.json()["active"] is False

    officers = client.get("/api/users/officers", headers=auth(token))
    assert officers.status_code == 200
    assert all(officer["active"] for officer in officers.json())
    assert created.json()["id"] not in [officer["id"] for officer in officers.json()]

    # The deactivated user must not be able to log in.
    blocked = client.post(
        "/api/auth/login",
        data={"username": "newofficer@samanvay.demo", "password": "OfficerPass123!"},
    )
    assert blocked.status_code == 400


def test_audit_logs(client):
    token = login(client)
    create_institution(client, token, "Audited Institute")

    logs = client.get("/api/audit-logs", headers=auth(token))
    assert logs.status_code == 200
    actions = [entry["action"] for entry in logs.json()]
    assert "LOGIN" in actions
    assert "CREATE" in actions
    assert any(entry["entity_type"] == "Institution" for entry in logs.json())

    filtered = client.get(
        "/api/audit-logs", headers=auth(token), params={"action": "CREATE"}
    )
    assert filtered.status_code == 200
    assert all(entry["action"] == "CREATE" for entry in filtered.json())


# ---------------------------------------------------------------------------
# Role based access control
# ---------------------------------------------------------------------------
def test_senior_management_is_read_only(client):
    token = login(client, "management@samanvay.demo")

    assert client.get("/api/complaints", headers=auth(token)).status_code == 200
    assert client.get("/api/dashboard/summary", headers=auth(token)).status_code == 200

    denied = client.post(
        "/api/institutions",
        headers=auth(token),
        json={"institution_name": "Blocked Institute"},
    )
    assert denied.status_code == 403

    complaint = create_complaint(client, login(client))
    denied_action = client.post(
        f"/api/complaints/{complaint['id']}/assign",
        headers=auth(token),
        json={"bureau_id": SEED["bureaus"][1]},
    )
    assert denied_action.status_code == 403


def test_bureau_admin_cannot_manage_users_or_bureaus(client):
    token = login(client, "bureauadmin@samanvay.demo")

    assert client.get("/api/audit-logs", headers=auth(token)).status_code == 200
    assert (
        client.post(
            "/api/users",
            headers=auth(token),
            json={
                "full_name": "Blocked User",
                "email": "blocked@samanvay.demo",
                "password": "BlockedPass123!",
                "role": "Senior Management",
            },
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/bureaus",
            headers=auth(token),
            json={"bureau_code": "BLK", "bureau_name": "Blocked Bureau"},
        ).status_code
        == 403
    )


def test_case_officer_can_write_cases(client):
    token = login(client, "officer@samanvay.demo")
    complaint = create_complaint(client, token)
    action = client.post(
        f"/api/complaints/{complaint['id']}/actions",
        headers=auth(token),
        json={"remarks": "Reviewed the submitted documents."},
    )
    assert action.status_code == 200
    assert (
        client.post(
            "/api/bureaus",
            headers=auth(token),
            json={"bureau_code": "NOP", "bureau_name": "Not Allowed"},
        ).status_code
        == 403
    )
    assert (
        client.get("/api/audit-logs", headers=auth(token)).status_code == 403
    )
