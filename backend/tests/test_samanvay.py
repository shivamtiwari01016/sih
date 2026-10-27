import pytest
from datetime import date, timedelta
import helpers
from helpers import auth, login

def test_samanvay_abac_sensitive_masking(client):
    """Ensure sensitive categories (Ragging/Whistleblower) mask description for non-holding bureau."""
    admin_token = login(client, "admin@samanvay.demo")

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
    regional_token = login(client, "regional@samanvay.demo")
    detail = client.get(f"/api/complaints/{case_id}", headers=auth(regional_token))
    assert detail.status_code == 200
    res = detail.json()

    # The description should be masked under Need-to-Know ABAC!
    assert "Protected case details" in res["description"]
    assert res["visibility_level"] == "L1_MASKED"
    assert res["category"] == "Ragging & Student Safety"


def test_samanvay_break_glass_protocol(client):
    """Test Break-Glass emergency override protocol with auditor alert."""
    admin_token = login(client, "admin@samanvay.demo")
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
    officer_token = login(client, "regional@samanvay.demo")
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
    admin_token = login(client, "admin@samanvay.demo")

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
    admin_token = login(client, "admin@samanvay.demo")
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
    admin_token = login(client, "admin@samanvay.demo")
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
    admin_token = login(client, "admin@samanvay.demo")
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


def test_institution_eda_shape_and_insufficient_data(client):
    """Test GET /api/institutions/{id}/eda shape and insufficient_data flag (< 5 complaints)."""
    admin_token = login(client, "admin@samanvay.demo")

    # 1. Create a brand new institution with 0 complaints
    new_inst = client.post(
        "/api/institutions",
        headers=auth(admin_token),
        json={
            "institution_name": "Test Engineering Institute for EDA",
            "aicte_permanent_id": "EDA-TEST-001",
            "institution_type": "Engineering",
            "state": "Maharashtra",
            "region": "West",
            "city": "Pune",
        },
    )
    assert new_inst.status_code == 201
    inst_id = new_inst.json()["id"]

    # 2. Call EDA endpoint on empty institution
    eda_resp = client.get(f"/api/institutions/{inst_id}/eda", headers=auth(admin_token))
    assert eda_resp.status_code == 200
    data = eda_resp.json()

    # Verify response schema shape
    assert "stats" in data
    for key in ("total", "open", "overdue", "disposed", "active_overlaps", "avg_open_age_days"):
        assert key in data["stats"], f"Missing {key} in stats"

    assert "monthly" in data
    assert isinstance(data["monthly"], list)
    assert len(data["monthly"]) == 12
    for m in data["monthly"]:
        assert "month" in m and "received" in m and "disposed" in m

    assert "by_category" in data and isinstance(data["by_category"], list)
    assert "by_bureau" in data and isinstance(data["by_bureau"], list)
    assert "by_status" in data and isinstance(data["by_status"], list)

    assert "ageing" in data
    for bucket in ("0-30", "31-60", "61-90", "90+"):
        assert bucket in data["ageing"], f"Missing {bucket} in ageing"

    assert "sla" in data
    assert "within_sla_pct" in data["sla"]
    assert "all_institutions_avg_pct" in data["sla"]

    assert "peer" in data
    assert "institution_count" in data["peer"]
    assert "state_avg_count" in data["peer"]
    assert "state_avg_risk" in data["peer"]

    assert "insights" in data
    assert isinstance(data["insights"], list)
    assert len(data["insights"]) <= 4

    # Verify insufficient_data flag is True when total < 5
    assert data["stats"]["total"] == 0
    assert data["insufficient_data"] is True

    # 3. Add 5 complaints to cross the threshold
    for i in range(5):
        c_resp = client.post(
            "/api/complaints",
            headers=auth(admin_token),
            json={
                "institution_id": inst_id,
                "category": "Infrastructure" if i % 2 == 0 else "Fee Structure",
                "subject": f"EDA Test Case {i+1}",
                "description": f"Detailed description for complaint number {i+1}.",
                "assigned_bureau_id": helpers.SEED["bureaus"][0],
                "priority": "Medium",
            },
        )
        assert c_resp.status_code == 201

    # 4. Verify insufficient_data is now False with 5 complaints
    eda_resp_5 = client.get(f"/api/institutions/{inst_id}/eda", headers=auth(admin_token))
    assert eda_resp_5.status_code == 200
    data_5 = eda_resp_5.json()
    assert data_5["stats"]["total"] == 5
    assert data_5["insufficient_data"] is False
    assert len(data_5["by_category"]) > 0


def test_institution_eda_abac_and_no_pii_leakage(client):
    """Test that EDA and complaints never leak complainant PII and respect ABAC for sensitive cases."""
    admin_token = login(client, "admin@samanvay.demo")
    regional_token = login(client, "regional@samanvay.demo")

    # Create institution
    inst_resp = client.post(
        "/api/institutions",
        headers=auth(admin_token),
        json={
            "institution_name": "ABAC Sensitive Security College",
            "aicte_permanent_id": "SEC-TEST-999",
            "state": "Delhi",
            "region": "North",
        },
    )
    inst_id = inst_resp.json()["id"]

    # Create sensitive complaint with sensitive subject and confidential matter in Bureau 0
    client.post(
        "/api/complaints",
        headers=auth(admin_token),
        json={
            "institution_id": inst_id,
            "category": "Ragging & Student Safety",
            "sensitivity": "Ragging",
            "subject": "Extremely Confidential Whistleblower Allegation",
            "description": "Complainant John Doe (ID: 998877) reported hazing in room 402.",
            "assigned_bureau_id": helpers.SEED["bureaus"][0],
        },
    )

    # 1. Fetch EDA endpoint as regional officer (Bureau 1 - non-holding bureau)
    eda_resp = client.get(f"/api/institutions/{inst_id}/eda", headers=auth(regional_token))
    assert eda_resp.status_code == 200
    eda_json = eda_resp.text

    # No PII leakage: no personal names, phone numbers, or pseudo IDs
    assert "John Doe" not in eda_json
    assert "998877" not in eda_json
    assert "complainant_encrypted" not in eda_json
    assert "complainant_pseudo_id" not in eda_json

    # 2. Fetch institution complaints list as non-holding bureau officer
    comp_list = client.get(f"/api/institutions/{inst_id}/complaints", headers=auth(regional_token))
    assert comp_list.status_code == 200
    items = comp_list.json()
    assert len(items) == 1
    # Subject should be masked under Need-to-Know ABAC
    assert "Confidential Whistleblower Allegation" not in items[0]["subject"]
    assert "Sensitive Matter" in items[0]["subject"]
    assert items[0]["category"] == "Ragging & Student Safety"

