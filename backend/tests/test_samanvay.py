import pytest
from datetime import date, timedelta
import helpers
from helpers import auth, login

def test_samanvay_abac_sensitive_masking(client):
    """Ensure sensitive categories (Ragging/Whistleblower) mask description for non-holding bureau."""
    admin_token = login(client, "admin@test.demo")

    # Create a sensitive complaint in Regulation Bureau (bureau 0)
    created = client.post(
        "/api/complaints",
        headers=auth(admin_token),
        json={
            "institution_id": helpers.SEED["institution"],
            "category": "Ragging & Student Safety",
            "sensitivity": "Ragging",
            "subject": "Hostel Ragging Incident",
            "description": "Sensitive details of harassment in hostel block C.",
            "assigned_bureau_id": helpers.SEED["bureaus"][0],
            "priority": "High",
        },
    )
    assert created.status_code == 201
    case_id = created.json()["id"]

    # Now login as officer in another bureau (bureau 1)
    # user[4] is in bureau 1 (regional)
    regional_token = login(client, "regional@test.demo")
    detail = client.get(f"/api/complaints/{case_id}", headers=auth(regional_token))
    assert detail.status_code == 200
    res = detail.json()

    # The description should be masked under Need-to-Know ABAC!
    assert "Protected case details" in res["description"]
    assert res["visibility_level"] == "L1_MASKED"
    assert res["category"] == "Ragging & Student Safety"


def test_samanvay_break_glass_protocol(client):
    """Test Break-Glass emergency override protocol with auditor alert."""
    admin_token = login(client, "admin@test.demo")
    created = client.post(
        "/api/complaints",
        headers=auth(admin_token),
        json={
            "institution_id": helpers.SEED["institution"],
            "category": "Whistleblower Fraud",
            "sensitivity": "Whistleblower",
            "subject": "Confidential financial misappropriation",
            "description": "Evidence of diverted student scholarship funds to private accounts.",
            "assigned_bureau_id": helpers.SEED["bureaus"][0],
        },
    )
    case_id = created.json()["id"]

    # Officer triggers break glass
    officer_token = login(client, "regional@test.demo")
    bg_resp = client.post(
        f"/api/complaints/{case_id}/break-glass",
        headers=auth(officer_token),
        json={"reason": "Emergency regulatory inspection ordered by Central Vigilance"},
    )
    assert bg_resp.status_code == 200
    assert "Emergency Break-Glass access logged and granted" in bg_resp.json()["message"]
    assert "diverted student scholarship" in bg_resp.json()["case"]["description"]

    # Verify audit log verification
    integrity = client.get("/api/audit-logs/verify-integrity", headers=auth(admin_token))
    print("INTEGRITY JSON:", integrity.json())
    assert integrity.status_code == 200
    assert integrity.json()["verified"] is True


def test_samanvay_action_intent_conflict_detection(client):
    """Test Action Intent card conflict warning between different bureaus."""
    admin_token = login(client, "admin@test.demo")

    # Register an open case in Regulation Bureau
    c1 = client.post(
        "/api/complaints",
        headers=auth(admin_token),
        json={
            "institution_id": helpers.SEED["institution"],
            "category": "Fee Structure",
            "subject": "Excessive Examination Fee",
            "description": "Tuition overcharge beyond approved fees.",
            "assigned_bureau_id": helpers.SEED["bureaus"][0],
        },
    ).json()

    # Register an open case in PGRC (bureau 1)
    c2 = client.post(
        "/api/complaints",
        headers=auth(admin_token),
        json={
            "institution_id": helpers.SEED["institution"],
            "category": "Affiliation & Norms",
            "subject": "Deficient laboratory infrastructure",
            "description": "Laboratory facilities lack computers.",
            "assigned_bureau_id": helpers.SEED["bureaus"][1],
        },
    ).json()

    # PGRC registers an intent for closure
    intent_resp = client.post(
        f"/api/complaints/{c2['id']}/intents",
        headers=auth(admin_token),
        json={
            "intent_type": "Closure",
            "planned_date": (date.today() + timedelta(days=14)).isoformat(),
            "remarks": "Proposing closure of engineering wing",
        },
    )
    assert intent_resp.status_code == 200
    conflicts = intent_resp.json()["conflicts_detected"]
    assert len(conflicts) >= 1
    assert any("Regulation Bureau" in c for c in conflicts)


def test_samanvay_coordination_room_and_joint_decision(client):
    """Test coordination room lifecycle and joint decision written to both cases' timelines."""
    admin_token = login(client, "admin@test.demo")
    c1 = client.post(
        "/api/complaints",
        headers=auth(admin_token),
        json={
            "institution_id": helpers.SEED["institution"],
            "category": "Fee Structure",
            "subject": "Case 1: Fee refund delay",
            "description": "Students awaiting caution money return.",
            "assigned_bureau_id": helpers.SEED["bureaus"][0],
        },
    ).json()

    c2 = client.post(
        "/api/complaints",
        headers=auth(admin_token),
        json={
            "institution_id": helpers.SEED["institution"],
            "category": "Fee Structure",
            "subject": "Case 2: Illegal fee fine",
            "description": "College levied fine for late registration.",
            "assigned_bureau_id": helpers.SEED["bureaus"][1],
        },
    ).json()

    overlaps = client.get("/api/overlaps", headers=auth(admin_token)).json()
    assert len(overlaps) >= 1
    overlap_id = overlaps[0]["id"]

    # Coordination room details
    room = client.get(f"/api/overlaps/{overlap_id}/coordination-room", headers=auth(admin_token))
    assert room.status_code == 200
    room_data = room.json()
    assert "differences" in room_data
    assert "merged_timeline" in room_data
    assert "playbook_suggestion" in room_data

    # Joint decision
    decide = client.post(
        f"/api/overlaps/{overlap_id}/decide",
        headers=auth(admin_token),
        json={
            "decision_text": "PGRC to lead student fee inquiry; RB pauses compliance notice until 15 Nov.",
            "lead_bureau_code": "PGRC",
        },
    )
    assert decide.status_code == 200

    # Verify decision recorded on Case 1 timeline
    detail1 = client.get(f"/api/complaints/{c1['id']}", headers=auth(admin_token)).json()
    actions1 = [a["action_type"] for a in detail1["actions"]]
    assert "Joint Bureau Decision" in actions1


def test_samanvay_pre_check_live_banner(client):
    """Test pre-save live banner check in <= 30 seconds."""
    admin_token = login(client, "admin@test.demo")
    client.post(
        "/api/complaints",
        headers=auth(admin_token),
        json={
            "institution_id": helpers.SEED["institution"],
            "category": "Fee Structure",
            "subject": "Pre-check fee complaint",
            "description": "Excessive fee charged.",
            "assigned_bureau_id": helpers.SEED["bureaus"][0],
        },
    )

    pre_check = client.post(
        "/api/complaints/check-overlap-live",
        headers=auth(admin_token),
        json={
            "institution_id": helpers.SEED["institution"],
            "category": "Fee Structure",
            "subject": "Second fee complaint",
            "assigned_bureau_id": helpers.SEED["bureaus"][1],
        },
    )
    assert pre_check.status_code == 200
    assert pre_check.json()["has_conflicts"] is True
    assert len(pre_check.json()["warnings"]) >= 1


def test_samanvay_nl_search(client):
    """Test Natural Language search parsing."""
    admin_token = login(client, "admin@test.demo")
    nl_res = client.get(
        "/api/complaints/nl-search",
        headers=auth(admin_token),
        params={"query": "pending fee complaints in Maharashtra older than 5 days"},
    )
    assert nl_res.status_code == 200
    data = nl_res.json()
    assert "filters_applied" in data
    assert data["filters_applied"].get("category") == "Fee"
    assert data["filters_applied"].get("state") == "Maharashtra"
