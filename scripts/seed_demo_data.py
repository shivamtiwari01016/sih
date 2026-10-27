#!/usr/bin/env python3
"""Samanvay (समन्वय) - Secure Complaint Coordination System for AICTE
High-fidelity deterministic seed data generator.
Creates:
- 4 Bureaus (Regulation, PGRC, Approval, Regional)
- 40 Users across all ABAC roles (RB, PGRC, Regional, Mgmt, Admin, Auditor)
- 300 Institutions across all Indian states/regions with lat/lng, AICTE IDs, and aliases
- 650 Complaints with realistic distributions, DPDP encryption, SLA rules
- 35+ Planted Overlaps (Exact AICTE ID, Fuzzy name, Semantic, Cross-bureau conflicts, Sensitive, Coordinated rings)
- Planted showcase institution "ABC Institute of Technology" and PGRC fee extortion case
- Action Intents, Coordination Messages, Joint Decisions, Watchlists
- 2,150+ Tamper-evident Hash-chained Audit Logs
"""
import base64
import hashlib
import json
import os
import random
import sys
import uuid
from datetime import date, datetime, time, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if not os.path.isdir(BACKEND_DIR):
    BACKEND_DIR = BASE_DIR
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(
        BACKEND_DIR, "civicresolve.db"
    )

from app.core.database import Base, SessionLocal, engine
from app.core.migrations import run_light_migrations
from app.core.security import get_password_hash
from app.models import (
    AccessRequest,
    ActionIntent,
    AuditLog,
    Bureau,
    BureauTransfer,
    CaseAction,
    Complaint,
    ComplaintStatus,
    CoordinationDecision,
    CoordinationMessage,
    Document,
    Institution,
    IntentStatus,
    IntentType,
    Notification,
    NotificationType,
    OverlapFeedback,
    Priority,
    RelatedCase,
    RelationshipType,
    ReviewStatus,
    Sensitivity,
    SlaRule,
    TransferStatus,
    User,
    UserRole,
    Watchlist,
)
from app.utils.helpers import (
    GENESIS_HASH,
    encrypt_data,
    generate_pseudo_id,
    notify,
)
from institution_catalog import CATALOG

# Fixed seed for 100% deterministic reproducibility
random.seed(42)

DEMO_PASSWORD_HASH = get_password_hash("DemoPass123!")

INDIAN_CITIES = [
    # city, state, region, lat, lng
    ("Pune", "Maharashtra", "West", 18.5204, 73.8567),
    ("Mumbai", "Maharashtra", "West", 19.0760, 72.8777),
    ("Nagpur", "Maharashtra", "West", 21.1458, 79.0882),
    ("Nashik", "Maharashtra", "West", 19.9975, 73.7898),
    ("Aurangabad", "Maharashtra", "West", 19.8762, 75.3433),
    ("Bengaluru", "Karnataka", "South", 12.9716, 77.5946),
    ("Mysuru", "Karnataka", "South", 12.2958, 76.6394),
    ("Mangaluru", "Karnataka", "South", 12.9141, 74.8560),
    ("Hubballi", "Karnataka", "South", 15.3647, 75.1240),
    ("Chennai", "Tamil Nadu", "South", 13.0827, 80.2707),
    ("Coimbatore", "Tamil Nadu", "South", 11.0168, 76.9558),
    ("Madurai", "Tamil Nadu", "South", 9.9252, 78.1198),
    ("Tiruchirappalli", "Tamil Nadu", "South", 10.7905, 78.7047),
    ("Hyderabad", "Telangana", "South", 17.3850, 78.4867),
    ("Warangal", "Telangana", "South", 17.9689, 79.5941),
    ("Visakhapatnam", "Andhra Pradesh", "South", 17.6868, 83.2185),
    ("Vijayawada", "Andhra Pradesh", "South", 16.5062, 80.6480),
    ("New Delhi", "Delhi", "North", 28.6139, 77.2090),
    ("Noida", "Uttar Pradesh", "North", 28.5355, 77.3910),
    ("Greater Noida", "Uttar Pradesh", "North", 28.4744, 77.5040),
    ("Lucknow", "Uttar Pradesh", "North", 26.8467, 80.9462),
    ("Kanpur", "Uttar Pradesh", "North", 26.4499, 80.3319),
    ("Varanasi", "Uttar Pradesh", "North", 25.3176, 82.9739),
    ("Jaipur", "Rajasthan", "North-West", 26.9124, 75.7873),
    ("Jodhpur", "Rajasthan", "North-West", 26.2389, 73.0243),
    ("Kota", "Rajasthan", "North-West", 25.2138, 75.8648),
    ("Bhopal", "Madhya Pradesh", "Central", 23.2599, 77.4126),
    ("Indore", "Madhya Pradesh", "Central", 22.7196, 75.8577),
    ("Jabalpur", "Madhya Pradesh", "Central", 23.1815, 79.9864),
    ("Ahmedabad", "Gujarat", "West", 23.0225, 72.5714),
    ("Vadodara", "Gujarat", "West", 22.3072, 73.1812),
    ("Surat", "Gujarat", "West", 21.1702, 72.8311),
    ("Kolkata", "West Bengal", "East", 22.5726, 88.3639),
    ("Durgapur", "West Bengal", "East", 23.5204, 87.3119),
    ("Bhubaneswar", "Odisha", "East", 20.2961, 85.8245),
    ("Patna", "Bihar", "East", 25.5941, 85.1376),
    ("Ranchi", "Jharkhand", "East", 23.3441, 85.3096),
    ("Guwahati", "Assam", "North-East", 26.1445, 91.7362),
    ("Chandigarh", "Chandigarh", "North", 30.7333, 76.7794),
    ("Thiruvananthapuram", "Kerala", "South", 8.5241, 76.9366),
    ("Kochi", "Kerala", "South", 9.9312, 76.2673),
]

NAME_PREFIXES = [
    "Shri", "Sri", "Swami", "Mahatma", "Sardar", "Dr.", "Aryabhatta",
    "Ramanujan", "Visvesvaraya", "APJ Abdul Kalam", "Tagore", "Vivekananda",
    "B.R. Ambedkar", "Chhatrapati Shivaji", "Lokmanya", "Birla", "Tata",
    "Amity", "Bharati", "PES", "Manipal", "Vellore", "Kalinga", "Thapar",
    "Symbiosis", "D.Y. Patil", "MIT", "Sinhgad", "KLE", "SRM", "Lovely",
]

NAME_SUFFIXES = [
    ("Institute of Technology", "Inst. of Tech", "इंजीनियरिंग संस्थान"),
    ("College of Engineering", "Coll. of Engg", "अभियांत्रिकी महाविद्यालय"),
    ("Institute of Technology and Management", "Inst. of Tech & Mgmt", "प्रौद्योगिकी एवं प्रबंधन संस्थान"),
    ("Polytechnic Institute", "Polytechnic Inst.", "पॉलीटेक्निक संस्थान"),
    ("Institute of Engineering and Technology", "Inst. of Engg & Tech", "अभियांत्रिकी एवं प्रौद्योगिकी संस्थान"),
    ("Academy of Technical Education", "Acad. of Tech. Edu", "तकनीकी शिक्षा अकादमी"),
]


def generate_institutions():
    """Build ~300 curated and generated institutions with coordinates, AICTE IDs, and aliases."""
    institutions = []
    seen_names = set()
    seen_norm_names = set()

    # 1. Planted Showcase College: "ABC Institute of Technology"
    seen_names.add("ABC Institute of Technology")
    seen_norm_names.add("abc institute of technology")
    institutions.append({
        "institution_name": "ABC Institute of Technology",
        "normalized_name": "abc institute of technology",
        "aicte_permanent_id": "1-1092837465",
        "aliases": ["A.B.C. Inst. of Tech", "ABC College of Engineering", "एबीसी इंस्टीट्यूट ऑफ टेक्नोलॉजी"],
        "institution_type": "Engineering",
        "address": "Survey No. 42, Hinjewadi Phase 1, Pune, Maharashtra 411057",
        "city": "Pune",
        "state": "Maharashtra",
        "region": "West",
        "district": "Pune",
        "website": "https://abctech.edu.in",
        "established_year": 2004,
        "ownership": "Private-Unaided",
        "affiliation": "Savitribai Phule Pune University",
        "institution_status": "Active",
        "lat": 18.5204,
        "lng": 73.8567,
    })

    # 2. Add catalog items (156 institutions)
    for idx, item in enumerate(CATALOG):
        name = item["institution_name"].strip()
        norm = name.lower()
        if name in seen_names or norm in seen_norm_names:
            continue
        seen_names.add(name)
        seen_norm_names.add(norm)

        city_match = next((c for c in INDIAN_CITIES if c[0].lower() == (item.get("city") or "").lower()), None)
        if not city_match:
            city_match = random.choice(INDIAN_CITIES)
        
        aicte_id = f"1-{1000000000 + idx * 7919 % 899999999}"
        aliases = []
        if "institute" in norm:
            aliases.append(name.replace("Institute", "Inst."))
        if "engineering" in norm:
            aliases.append(name.replace("Engineering", "Engg"))
        if "technology" in norm:
            aliases.append(name.replace("Technology", "Tech"))
        
        institutions.append({
            "institution_name": name,
            "normalized_name": norm,
            "aicte_permanent_id": aicte_id,
            "aliases": aliases,
            "institution_type": item.get("institution_type") or "Engineering",
            "address": item.get("address") or f"{city_match[0]}, {city_match[1]}",
            "city": item.get("city") or city_match[0],
            "state": item.get("state") or city_match[1],
            "region": item.get("region") or city_match[2],
            "district": item.get("district") or item.get("city") or city_match[0],
            "website": item.get("website"),
            "established_year": item.get("established_year") or random.randint(1960, 2018),
            "ownership": item.get("ownership") or "Private-Unaided",
            "affiliation": item.get("affiliation") or "State Technological University",
            "institution_status": "Active",
            "lat": city_match[3] + round(random.uniform(-0.06, 0.06), 4),
            "lng": city_match[4] + round(random.uniform(-0.06, 0.06), 4),
        })

    # Ensure Institute of Chemical Technology is present
    if not any(i["institution_name"] == "Institute of Chemical Technology" for i in institutions):
        ict_name = "Institute of Chemical Technology"
        seen_names.add(ict_name)
        seen_norm_names.add(ict_name.lower())
        institutions.append({
            "institution_name": ict_name,
            "normalized_name": ict_name.lower(),
            "aicte_permanent_id": "1-1092837499",
            "aliases": ["ICT Mumbai", "ICT", "इंस्टीट्यूट ऑफ केमिकल टेक्नोलॉजी"],
            "institution_type": "Deemed University",
            "address": "Nathalal Parekh Marg, Matunga, Mumbai 400019",
            "city": "Mumbai",
            "state": "Maharashtra",
            "region": "West",
            "district": "Mumbai City",
            "website": "https://www.ictmumbai.edu.in",
            "established_year": 1933,
            "ownership": "Government",
            "affiliation": "Deemed University (Autonomous)",
            "institution_status": "Active",
            "lat": 19.0222,
            "lng": 72.8561,
        })

    # 3. Generate up to 305 unique institutions
    curr_id = 2000
    while len(institutions) < 305:
        city_info = random.choice(INDIAN_CITIES)
        prefix = random.choice(NAME_PREFIXES)
        suffix_full, suffix_abbr, suffix_hi = random.choice(NAME_SUFFIXES)
        name = f"{prefix} {suffix_full}"
        suffix_count = 1
        while name in seen_names or name.lower() in seen_norm_names:
            name = f"{prefix} {city_info[0]} {suffix_full}"
            if name in seen_names or name.lower() in seen_norm_names:
                suffix_count += 1
                name = f"{prefix} Campus-{suffix_count} {suffix_full}"
        seen_names.add(name)
        seen_norm_names.add(name.lower())
        
        norm = name.lower()
        aicte_id = f"1-{3000000000 + curr_id * 31337 % 899999999}"
        curr_id += 1
        
        aliases = [
            f"{prefix} {suffix_abbr}",
            f"{prefix} {suffix_hi}",
        ]
        
        institutions.append({
            "institution_name": name,
            "normalized_name": norm,
            "aicte_permanent_id": aicte_id,
            "aliases": aliases,
            "institution_type": "Engineering" if "Engineering" in name or "Tech" in name else "Management",
            "address": f"Campus Road, Sector {random.randint(1, 45)}, {city_info[0]}, {city_info[1]}",
            "city": city_info[0],
            "state": city_info[1],
            "region": city_info[2],
            "district": city_info[0],
            "website": f"https://www.{norm.replace(' ', '')[:15]}.edu.in",
            "established_year": random.randint(1985, 2020),
            "ownership": random.choice(["Private-Unaided", "Private-Aided", "Government"]),
            "affiliation": f"{city_info[1]} Technical University",
            "institution_status": "Active",
            "lat": city_info[3] + round(random.uniform(-0.08, 0.08), 4),
            "lng": city_info[4] + round(random.uniform(-0.08, 0.08), 4),
        })

    return institutions


def seed_data():
    print("=" * 70)
    print("Initializing Samanvay (समन्वय) Database Seeder...")
    print("=" * 70)

    Base.metadata.create_all(bind=engine)
    run_light_migrations()
    db = SessionLocal()

    try:
        print("[1/8] Clearing existing records...")
        for model in (
            CoordinationDecision,
            CoordinationMessage,
            ActionIntent,
            OverlapFeedback,
            AccessRequest,
            Watchlist,
            SlaRule,
            AuditLog,
            Notification,
            Document,
            BureauTransfer,
            RelatedCase,
            CaseAction,
            Complaint,
            User,
            Institution,
            Bureau,
        ):
            db.query(model).delete()
        db.commit()

        print("[2/8] Creating AICTE Bureaus...")
        bureaus_data = [
            ("REG", "Regulation Bureau", "Handles regulatory compliance, AICTE approval norms, intake violations, fee caps"),
            ("PGRC", "Public Grievance Redressal Cell", "Handles citizen, student, and faculty complaints, fee extortion, certificates withholding"),
            ("APB", "Approval Process Bureau", "Handles annual institutional approvals, faculty verification, infrastructure compliance"),
            ("RO", "Regional Offices", "Handles local jurisdiction inspections, regional vigilance, state coordination"),
        ]
        bureaus = {}
        for code, name, desc in bureaus_data:
            b = Bureau(bureau_code=code, bureau_name=name, description=desc)
            db.add(b)
            db.flush()
            bureaus[code] = b
        db.commit()

        print("[3/8] Creating SLA Rules...")
        sla_specs = [
            ("Fee Structure", 30, 24),
            ("Faculty Related", 45, 48),
            ("Infrastructure", 45, 48),
            ("Admission", 30, 24),
            ("Examination", 30, 24),
            ("Affiliation", 60, 48),
            ("Ragging", 7, 12),
            ("Harassment", 7, 12),
            ("Whistleblower", 15, 12),
        ]
        for cat, d_disp, h_ack in sla_specs:
            db.add(SlaRule(category=cat, days_to_dispose=d_disp, ack_hours_for_overlap=h_ack))
        db.commit()

        print("[4/8] Creating 40 Users across all ABAC Roles...")
        # Core pitch demo users
        users_list = [
            # Full Name, Email, Role, BureauCode, Region, MFA
            ("R.K. Sharma", "sharma@samanvay.demo", UserRole.RB_OFFICER, "REG", "North", False),
            ("Sunita Verma", "verma@samanvay.demo", UserRole.PGRC_OFFICER, "PGRC", "North", False),
            ("Kirit Patel", "patel@samanvay.demo", UserRole.REGIONAL_OFFICER, "RO", "West", False),
            ("Dr. Ramesh Rao", "rao@samanvay.demo", UserRole.SENIOR_MANAGEMENT, None, None, False),
            ("System Admin", "admin@samanvay.demo", UserRole.SUPER_ADMIN, None, None, False),
            ("Chief Vigilance Auditor", "auditor@samanvay.demo", UserRole.AUDITOR, None, None, False),
            # Demo aliases
            ("Officer Demo", "officer@samanvay.demo", UserRole.CASE_OFFICER, "REG", None, False),
            ("Regional Demo", "regional@samanvay.demo", UserRole.REGIONAL_OFFICER, "RO", "West", False),
            ("PGRC Demo", "pgrc@samanvay.demo", UserRole.PGRC_OFFICER, "PGRC", None, False),
            ("Mgmt Demo", "management@samanvay.demo", UserRole.SENIOR_MANAGEMENT, None, None, False),
            ("Officer 1", "officer1@samanvay.demo", UserRole.CASE_OFFICER, "REG", None, False),
            ("Regulation Admin", "regadmin@samanvay.demo", UserRole.BUREAU_ADMIN, "REG", None, False),
            ("PGRC Admin", "pgrcadmin@samanvay.demo", UserRole.BUREAU_ADMIN, "PGRC", None, False),
            ("Bureau Admin", "bureauadmin@samanvay.demo", UserRole.BUREAU_ADMIN, "REG", None, False),
            ("Samanvay Admin", "superadmin@samanvay.demo", UserRole.SUPER_ADMIN, None, None, False),
        ]

        # Additional officers to make 40 users across Indian regions
        officer_names = [
            ("Anil Deshmukh", "West", "REG"), ("Pooja Kulkarni", "West", "PGRC"),
            ("Rajesh Nair", "South", "RO"), ("Deepa Sundaram", "South", "REG"),
            ("Amitabh Banerjee", "East", "PGRC"), ("Subhashree Das", "East", "RO"),
            ("Manpreet Singh", "North", "REG"), ("Harleen Kaur", "North", "PGRC"),
            ("Vikram Rathore", "North-West", "RO"), ("Ananya Joshi", "Central", "REG"),
            ("Gaurav Saxena", "Central", "PGRC"), ("Tenzing Norbu", "North-East", "RO"),
            ("Bipul Saikia", "North-East", "REG"), ("Kavita Reddy", "South", "PGRC"),
            ("Suresh Meena", "North-West", "REG"), ("Alok Tripathi", "North", "RO"),
            ("Naveen Chhabra", "North", "REG"), ("Smita Patil", "West", "RO"),
            ("Vijay Shenoy", "South", "REG"), ("Arun Ghosh", "East", "REG"),
            ("Manish Tiwari", "Central", "RO"), ("Geeta Sen", "East", "PGRC"),
            ("Raghavendra Rao", "South", "RO"), ("Nandita Bose", "East", "RO"),
        ]

        for name, region, bcode in officer_names:
            email_prefix = name.lower().replace(" ", ".")
            role = UserRole.REGIONAL_OFFICER if bcode == "RO" else (UserRole.RB_OFFICER if bcode == "REG" else UserRole.PGRC_OFFICER)
            users_list.append((name, f"{email_prefix}@samanvay.demo", role, bcode, region, False))

        user_objects = {}
        for name, email, role, bcode, region, mfa in users_list:
            u = User(
                full_name=name,
                email=email,
                password_hash=DEMO_PASSWORD_HASH,
                role=role,
                bureau_id=bureaus[bcode].id if bcode and bcode in bureaus else None,
                region_permissions=region,
                active=True,
                mfa_enabled=mfa,
            )
            db.add(u)
            db.flush()
            user_objects[email] = u
        db.commit()
        print(f"Created {len(user_objects)} users.")

        print("[5/8] Seeding 300+ Institutions across India with lat/lng & aliases...")
        inst_records = generate_institutions()
        institutions = []
        inst_by_name = {}
        for item in inst_records:
            inst = Institution(
                institution_name=item["institution_name"],
                normalized_name=item["normalized_name"],
                aicte_permanent_id=item["aicte_permanent_id"],
                aliases=json.dumps(item["aliases"]),
                institution_type=item["institution_type"],
                address=item["address"],
                city=item["city"],
                state=item["state"],
                region=item["region"],
                district=item["district"],
                website=item["website"],
                established_year=item["established_year"],
                ownership=item["ownership"],
                affiliation=item["affiliation"],
                institution_status=item["institution_status"],
                lat=item["lat"],
                lng=item["lng"],
            )
            db.add(inst)
            db.flush()
            institutions.append(inst)
            inst_by_name[inst.institution_name] = inst
        db.commit()
        print(f"Created {len(institutions)} institutions.")

        abc_inst = inst_by_name["ABC Institute of Technology"]

        # Watchlist entry for demo
        db.add(Watchlist(user_id=user_objects["sharma@samanvay.demo"].id, institution_id=abc_inst.id))
        db.add(Watchlist(user_id=user_objects["rao@samanvay.demo"].id, institution_id=abc_inst.id))
        db.commit()

        print("[6/8] Generating 650 Complaints with realistic SLA, encryption & planted overlaps...")
        complaints = []
        today = date.today()

        # Complaints counter to guarantee uniqueness
        comp_seq = 1

        def next_num(bcode):
            nonlocal comp_seq
            num = f"{bcode}-{today.year}-{comp_seq:06d}"
            comp_seq += 1
            return num

        # PLANT SHOWCASE COMPLAINT 1: ABC Inst. PGRC Fee Extortion Case (received 14 days ago)
        rec_14 = today - timedelta(days=14)
        abc_pgrc_case = Complaint(
            complaint_number=next_num("PGRC"),
            institution_id=abc_inst.id,
            received_date=rec_14,
            source_channel="National Grievance Portal",
            category="Fee Structure",
            subject="Illegal Capitation Fee and Admit Card Withholding",
            description=(
                "Final year computer engineering students are being forced to pay an unapproved INR 1,50,000 "
                "capitation fee under the guise of 'Special Infrastructure Levy'. The college administration "
                "threatens to withhold hall tickets and exam admit cards if not deposited immediately in cash."
            ),
            summary="Fee extortion: Students forced to pay ₹1.5L unapproved infrastructure levy under threat of exam admit card withholding.",
            priority=Priority.HIGH,
            sensitivity=Sensitivity.NORMAL,
            current_status=ComplaintStatus.UNDER_PROCESS,
            assigned_bureau_id=bureaus["PGRC"].id,
            assigned_officer_id=user_objects["verma@samanvay.demo"].id,
            expected_disposal_date=today + timedelta(days=16),
            last_action_at=datetime.combine(rec_14 + timedelta(days=7), time(14, 30)),
            next_action="Awaiting explanation from college principal; personal hearing proposed",
            complainant_pseudo_id=generate_pseudo_id(),
            complainant_encrypted=encrypt_data({"name": "Aarav Sharma & Batch", "mobile": "+91-9876543210"}),
            language="en",
            created_by=user_objects["verma@samanvay.demo"].id,
        )
        db.add(abc_pgrc_case)
        db.flush()
        complaints.append(abc_pgrc_case)

        # PLANT SHOWCASE COMPLAINT 2: ABC Instt of Tech RB Approval Violation Case (different wording, name typo in one)
        rec_20 = today - timedelta(days=20)
        abc_rb_case = Complaint(
            complaint_number=next_num("REG"),
            institution_id=abc_inst.id,
            received_date=rec_20,
            source_channel="Vigilance Directorate",
            category="Approval Norms",
            subject="Approval Norm Violation & Unauthorized Intake Expansion at ABC Instt of Tech",
            description=(
                "Comprehensive inspection report indicates ABC Instt of Tech has exceeded its approved "
                "sanctioned intake by 60 seats in Computer Science and operates unauthorized laboratories "
                "in violation of Approval Process Handbook Chapter 4 norms."
            ),
            summary="Regulatory inspection: ABC Instt of Tech running unapproved PG programs and violating intake quotas.",
            priority=Priority.HIGH,
            sensitivity=Sensitivity.NORMAL,
            current_status=ComplaintStatus.UNDER_PROCESS,
            assigned_bureau_id=bureaus["REG"].id,
            assigned_officer_id=user_objects["sharma@samanvay.demo"].id,
            expected_disposal_date=today + timedelta(days=10),
            last_action_at=datetime.combine(rec_20 + timedelta(days=10), time(11, 0)),
            next_action="Scrutiny of physical verification documents and show-cause notice",
            complainant_pseudo_id=generate_pseudo_id(),
            language="en",
            created_by=user_objects["sharma@samanvay.demo"].id,
        )
        db.add(abc_rb_case)
        db.flush()
        complaints.append(abc_rb_case)

        # PLANTED OVERLAP 1: Exact AICTE ID Match (RB side for another college)
        coll_exact = institutions[5]
        c_exact_rb = Complaint(
            complaint_number=next_num("REG"),
            institution_id=coll_exact.id,
            received_date=today - timedelta(days=25),
            source_channel="Direct Vigilance Report",
            category="Fee Structure",
            subject="Excess Tuition Collection Beyond State Fee Regulatory Committee Cap",
            description=f"Regulatory inspection confirms {coll_exact.institution_name} is collecting ₹95,000 extra per student beyond FRA approved limits.",
            summary="Regulatory audit identified capitation fee collection violating state limits.",
            priority=Priority.HIGH,
            sensitivity=Sensitivity.NORMAL,
            current_status=ComplaintStatus.UNDER_PROCESS,
            assigned_bureau_id=bureaus["REG"].id,
            assigned_officer_id=user_objects["sharma@samanvay.demo"].id,
            expected_disposal_date=today + timedelta(days=5),
            next_action="Issue Show Cause Notice",
            complainant_pseudo_id=generate_pseudo_id(),
            created_by=user_objects["sharma@samanvay.demo"].id,
        )
        c_exact_pgrc = Complaint(
            complaint_number=next_num("PGRC"),
            institution_id=coll_exact.id,
            received_date=today - timedelta(days=20),
            source_channel="Student Portal",
            category="Fee Structure",
            subject="Student Grievance on Extortionate Development Charges",
            description=f"Students of {coll_exact.institution_name} complain of mandatory demand for ₹95,000 development fee without receipts.",
            summary="Student grievance alleging ₹95k unreceipted development fees.",
            priority=Priority.HIGH,
            sensitivity=Sensitivity.NORMAL,
            current_status=ComplaintStatus.RECEIVED,
            assigned_bureau_id=bureaus["PGRC"].id,
            assigned_officer_id=user_objects["verma@samanvay.demo"].id,
            expected_disposal_date=today + timedelta(days=10),
            next_action="Scrutiny of complaint documents",
            complainant_pseudo_id=generate_pseudo_id(),
            created_by=user_objects["verma@samanvay.demo"].id,
        )
        db.add_all([c_exact_rb, c_exact_pgrc])
        db.flush()
        complaints.extend([c_exact_rb, c_exact_pgrc])

        # PLANTED OVERLAP 2: Fuzzy Name Match ("Shri Ramdeobaba Coll of Engg" vs full name)
        coll_fuzzy_1 = institutions[12]
        coll_fuzzy_2 = institutions[13]
        c_fuz_1 = Complaint(
            complaint_number=next_num("REG"),
            institution_id=coll_fuzzy_1.id,
            received_date=today - timedelta(days=30),
            source_channel="Email",
            category="Faculty Related",
            subject="Severe shortage of qualified PhD faculty in Computer Engineering",
            description=f"Inspection reveals 40% cadre ratio deficiency and unapproved ad-hoc faculty appointments.",
            summary="Faculty Cadre Ratio violation in CE department.",
            priority=Priority.MEDIUM,
            sensitivity=Sensitivity.NORMAL,
            current_status=ComplaintStatus.UNDER_PROCESS,
            assigned_bureau_id=bureaus["REG"].id,
            assigned_officer_id=user_objects["sharma@samanvay.demo"].id,
            expected_disposal_date=today + timedelta(days=15),
            complainant_pseudo_id=generate_pseudo_id(),
            created_by=user_objects["sharma@samanvay.demo"].id,
        )
        c_fuz_2 = Complaint(
            complaint_number=next_num("PGRC"),
            institution_id=coll_fuzzy_2.id,
            received_date=today - timedelta(days=18),
            source_channel="Letter",
            category="Faculty Related",
            subject="Non-payment of 7th Pay Commission salaries to assistant professors",
            description=f"Faculty association submits evidence of salary deductions and ghost teachers.",
            summary="Faculty salary underpayment and non-compliance with AICTE 7th CPC.",
            priority=Priority.HIGH,
            sensitivity=Sensitivity.NORMAL,
            current_status=ComplaintStatus.RECEIVED,
            assigned_bureau_id=bureaus["PGRC"].id,
            assigned_officer_id=user_objects["verma@samanvay.demo"].id,
            expected_disposal_date=today + timedelta(days=12),
            complainant_pseudo_id=generate_pseudo_id(),
            created_by=user_objects["verma@samanvay.demo"].id,
        )
        db.add_all([c_fuz_1, c_fuz_2])
        db.flush()
        complaints.extend([c_fuz_1, c_fuz_2])

        # PLANTED OVERLAP 3: Bilingual Semantic Match (Hindi & English fee issue)
        coll_bilingual = institutions[20]
        c_sem_en = Complaint(
            complaint_number=next_num("REG"),
            institution_id=coll_bilingual.id,
            received_date=today - timedelta(days=15),
            source_channel="Public Grievance",
            category="Fee Structure",
            subject="Excessive fee collection beyond approved capitation norms",
            description=f"College administration demanding extra unauthorized library and laboratory development deposit.",
            summary="Excessive fee collection violating AICTE regulatory mandate.",
            priority=Priority.HIGH,
            sensitivity=Sensitivity.NORMAL,
            current_status=ComplaintStatus.RECEIVED,
            assigned_bureau_id=bureaus["REG"].id,
            assigned_officer_id=user_objects["sharma@samanvay.demo"].id,
            expected_disposal_date=today + timedelta(days=15),
            language="en",
            complainant_pseudo_id=generate_pseudo_id(),
            created_by=user_objects["sharma@samanvay.demo"].id,
        )
        c_sem_hi = Complaint(
            complaint_number=next_num("PGRC"),
            institution_id=coll_bilingual.id,
            received_date=today - timedelta(days=12),
            source_channel="Letter",
            category="Fee Structure",
            subject="संस्थान द्वारा निर्धारित सीमा से अधिक अवैध शुल्क वसूली",
            description="महाविद्यालय प्रबंधन द्वारा छात्रों से पुस्तकालय और प्रयोगशाला के नाम पर अतिरिक्त अवैध शुल्क लिया जा रहा है। मना करने पर परीक्षा में न बैठने देने की धमकी दी जा रही है।",
            summary="हिंदी में प्राप्त शिकायत: निर्धारित सीमा से अधिक अवैध शुल्क वसूली और परीक्षा बहिष्कार की धमकी।",
            priority=Priority.HIGH,
            sensitivity=Sensitivity.NORMAL,
            current_status=ComplaintStatus.UNDER_PROCESS,
            assigned_bureau_id=bureaus["PGRC"].id,
            assigned_officer_id=user_objects["verma@samanvay.demo"].id,
            expected_disposal_date=today + timedelta(days=18),
            language="hi",
            complainant_pseudo_id=generate_pseudo_id(),
            created_by=user_objects["verma@samanvay.demo"].id,
        )
        db.add_all([c_sem_en, c_sem_hi])
        db.flush()
        complaints.extend([c_sem_en, c_sem_hi])

        # PLANTED OVERLAP 4: Cross-Bureau Conflict for Institute of Chemical Technology
        coll_conflict = inst_by_name.get("Institute of Chemical Technology", institutions[25])
        c_conf_rb = Complaint(
            complaint_number=next_num("REG"),
            institution_id=coll_conflict.id,
            received_date=today - timedelta(days=40),
            source_channel="Vigilance",
            category="Admission",
            subject="Irregular Admission Intake Exceeding Approved AICTE Seats at Institute of Chemical Technology",
            description="Admitted 30 extra students in chemical engineering technology beyond sanctioned intake capacity.",
            summary="Over-admission beyond AICTE approved intake at Institute of Chemical Technology.",
            priority=Priority.HIGH,
            sensitivity=Sensitivity.NORMAL,
            current_status=ComplaintStatus.UNDER_PROCESS,
            assigned_bureau_id=bureaus["REG"].id,
            assigned_officer_id=user_objects["sharma@samanvay.demo"].id,
            expected_disposal_date=today + timedelta(days=5),
            complainant_pseudo_id=generate_pseudo_id(),
            created_by=user_objects["sharma@samanvay.demo"].id,
        )
        c_conf_pgrc = Complaint(
            complaint_number=next_num("PGRC"),
            institution_id=coll_conflict.id,
            received_date=today - timedelta(days=35),
            source_channel="Parent Forum",
            category="Admission",
            subject="Refusal of Admission Cancellation and Non-Refund of Tuition Fee at Institute of Chemical Technology",
            description="College refused to refund ₹1,20,000 fee after student withdrew admission within cutoff date.",
            summary="Non-refund of fee on timely withdrawal of admission at Institute of Chemical Technology.",
            priority=Priority.MEDIUM,
            sensitivity=Sensitivity.NORMAL,
            current_status=ComplaintStatus.UNDER_PROCESS,
            assigned_bureau_id=bureaus["PGRC"].id,
            assigned_officer_id=user_objects["verma@samanvay.demo"].id,
            expected_disposal_date=today + timedelta(days=10),
            complainant_pseudo_id=generate_pseudo_id(),
            created_by=user_objects["verma@samanvay.demo"].id,
        )
        db.add_all([c_conf_rb, c_conf_pgrc])
        db.flush()
        complaints.extend([c_conf_rb, c_conf_pgrc])

        # PLANTED SENSITIVE CASES (Ragging & Whistleblower)
        coll_sens = institutions[30]
        c_ragging = Complaint(
            complaint_number=next_num("PGRC"),
            institution_id=coll_sens.id,
            received_date=today - timedelta(days=4),
            source_channel="Anti-Ragging Helpline",
            category="Ragging",
            subject="Hostel Severe Ragging and Psychological Harassment Incident",
            description="First year residential students physically intimidated and forced to perform humiliating tasks in hostel block B.",
            summary="Severe hostel ragging incident reported via 24x7 Helpline.",
            priority=Priority.URGENT,
            sensitivity=Sensitivity.RAGGING,
            current_status=ComplaintStatus.UNDER_PROCESS,
            assigned_bureau_id=bureaus["PGRC"].id,
            assigned_officer_id=user_objects["verma@samanvay.demo"].id,
            expected_disposal_date=today + timedelta(days=3),
            complainant_pseudo_id=generate_pseudo_id(),
            complainant_encrypted=encrypt_data({"victim": "Confidential Student Y", "contact": "+91-9988776655"}),
            created_by=user_objects["verma@samanvay.demo"].id,
        )
        c_whistleblower = Complaint(
            complaint_number=next_num("REG"),
            institution_id=coll_sens.id,
            received_date=today - timedelta(days=8),
            source_channel="Vigilance Commission",
            category="Whistleblower",
            subject="Confidential Whistleblower Disclosure: Embezzlement of Central Research Grants",
            description="Senior faculty reports systemic diversion of ₹2.4 Crores AICTE MODROBS and RPS research grants into fictitious equipment purchase accounts.",
            summary="Whistleblower disclosure on research grant misappropriation.",
            priority=Priority.URGENT,
            sensitivity=Sensitivity.WHISTLEBLOWER,
            current_status=ComplaintStatus.UNDER_PROCESS,
            assigned_bureau_id=bureaus["REG"].id,
            assigned_officer_id=user_objects["sharma@samanvay.demo"].id,
            expected_disposal_date=today + timedelta(days=7),
            complainant_pseudo_id=generate_pseudo_id(),
            complainant_encrypted=encrypt_data({"identity": "Protected Whistleblower X", "source": "Central Vigilance Commission"}),
            created_by=user_objects["sharma@samanvay.demo"].id,
        )
        db.add_all([c_ragging, c_whistleblower])
        db.flush()
        complaints.extend([c_ragging, c_whistleblower])

        # PLANTED COORDINATED COMPLAINT RING (5 nearly identical complaints)
        coll_ring = institutions[45]
        for ring_idx in range(5):
            c_ring = Complaint(
                complaint_number=next_num("PGRC"),
                institution_id=coll_ring.id,
                received_date=today - timedelta(days=2),
                source_channel="Online Portal",
                category="Infrastructure",
                subject="Substandard Hostel Food Quality and Unsanitary Canteen",
                description="The hostel mess serves substandard unhygienic food. Contaminated drinking water caused acute gastroenteritis among multiple students.",
                summary="Hostel mess food quality and unsanitary canteen conditions.",
                priority=Priority.MEDIUM,
                sensitivity=Sensitivity.NORMAL,
                current_status=ComplaintStatus.RECEIVED,
                assigned_bureau_id=bureaus["PGRC"].id,
                assigned_officer_id=user_objects["verma@samanvay.demo"].id,
                expected_disposal_date=today + timedelta(days=28),
                complainant_pseudo_id=generate_pseudo_id(),
                created_by=user_objects["verma@samanvay.demo"].id,
            )
            db.add(c_ring)
            db.flush()
            complaints.append(c_ring)

        # Standard Category & Status Distributions for remaining ~635 complaints
        categories = [
            ("Fee Structure", Priority.HIGH, 30),
            ("Faculty Related", Priority.MEDIUM, 45),
            ("Infrastructure", Priority.MEDIUM, 45),
            ("Admission", Priority.HIGH, 30),
            ("Examination", Priority.MEDIUM, 30),
            ("Affiliation", Priority.MEDIUM, 60),
            ("Whistleblower", Priority.URGENT, 15),
        ]
        status_weights = [
            (ComplaintStatus.RECEIVED, 0.40),
            (ComplaintStatus.UNDER_PROCESS, 0.30),
            (ComplaintStatus.DISPOSED, 0.20),
            (ComplaintStatus.TRANSFERRED, 0.05),
            (ComplaintStatus.ESCALATED, 0.05),
        ]
        status_pool = []
        for st, wt in status_weights:
            status_pool.extend([st] * int(wt * 100))

        officer_keys = [k for k in user_objects.keys() if "samanvay.demo" in k and "admin" not in k and "auditor" not in k]

        for _ in range(630):
            inst = random.choice(institutions)
            cat, prio, days_disp = random.choice(categories)
            status = random.choice(status_pool)
            days_ago = random.randint(1, 175)
            rec_date = today - timedelta(days=days_ago)

            # Make due dates relative to today so ~20% of open cases are overdue
            if status != ComplaintStatus.DISPOSED:
                if random.random() < 0.20:
                    exp_disp = today - timedelta(days=random.randint(1, 25))
                else:
                    exp_disp = today + timedelta(days=random.randint(2, days_disp))
            else:
                exp_disp = rec_date + timedelta(days=days_disp)

            b_key = random.choice(["REG", "PGRC", "RO", "APB"])
            bureau = bureaus[b_key]

            officer_email = random.choice(officer_keys)
            officer = user_objects[officer_email]

            disp_date = None
            if status == ComplaintStatus.DISPOSED:
                disp_days = min(days_ago - 1, random.randint(10, days_disp + 10))
                disp_date = datetime.combine(rec_date + timedelta(days=disp_days), time(16, 0))

            sens = Sensitivity.WHISTLEBLOWER if cat == "Whistleblower" else Sensitivity.NORMAL

            c = Complaint(
                complaint_number=next_num(b_key),
                institution_id=inst.id,
                received_date=rec_date,
                source_channel=random.choice(["Online Portal", "Email", "Direct Vigilance", "Letter", "Phone"]),
                category=cat,
                subject=f"Grievance regarding {cat.lower()} at {inst.institution_name}",
                description=(
                    f"Formal grievance submitted concerning non-compliance in {cat.lower()}. "
                    f"Institution: {inst.institution_name}, {inst.city}. "
                    f"Documentation and affidavits provided for regulatory scrutiny."
                ),
                summary=f"{cat} grievance concerning {inst.institution_name} in {inst.city}.",
                priority=prio,
                sensitivity=sens,
                current_status=status,
                assigned_bureau_id=bureau.id,
                assigned_officer_id=officer.id,
                expected_disposal_date=exp_disp,
                disposed_at=disp_date,
                created_by=officer.id,
                next_action="Awaiting compliance reply" if status != ComplaintStatus.DISPOSED else None,
                last_action_at=datetime.combine(rec_date + timedelta(days=random.randint(1, max(1, days_ago // 2))), time(11, 0)),
                complainant_pseudo_id=generate_pseudo_id(),
                language="en",
            )
            db.add(c)
            complaints.append(c)
            if len(complaints) % 150 == 0:
                db.flush()

        db.commit()
        print(f"Created {len(complaints)} complaints across all AICTE categories.")

        print("[7/8] Establishing Planted Overlaps, Coordination Rooms & Intent Cards...")
        planted_pairs = [
            (abc_pgrc_case, abc_rb_case, 0.95, ["Matching institution: ABC Institute of Technology vs ABC Instt of Tech (name typo match)", "Cross-bureau inquiry: PGRC fee extortion vs RB approval violation", "High jurisdictional overlap"], RelationshipType.CROSS_BUREAU_COORDINATION, ReviewStatus.SUGGESTED),
            (c_exact_rb, c_exact_pgrc, 0.96, ["Same verified AICTE ID", "Both cases active", "Different holding bureaus"], RelationshipType.CROSS_BUREAU_COORDINATION, ReviewStatus.CONFIRMED_RELATED),
            (c_fuz_1, c_fuz_2, 0.88, ["Fuzzy institutional name match (>85%)", "Same complaint category: Faculty Related", "Cross-bureau jurisdiction"], RelationshipType.CROSS_BUREAU_COORDINATION, ReviewStatus.SUGGESTED),
            (c_sem_en, c_sem_hi, 0.91, ["Bilingual semantic alignment: Capitation fee overcharge", "Same verified institution", "Cross-bureau overlap"], RelationshipType.CROSS_BUREAU_COORDINATION, ReviewStatus.CONFIRMED_RELATED),
            (c_conf_rb, c_conf_pgrc, 0.94, ["Institute of Chemical Technology", "Admission irregular seats vs lab fee refund conflict", "Conflicting regulatory intents"], RelationshipType.CROSS_BUREAU_COORDINATION, ReviewStatus.CONFIRMED_RELATED),
        ]

        # Additional synthetic overlaps
        seen_overlap_pairs = set()
        for c1, c2, score, reasons, rel_type, r_status in planted_pairs:
            pair = tuple(sorted([str(c1.id), str(c2.id)]))
            seen_overlap_pairs.add(pair)
            rc = RelatedCase(
                complaint_id_1=c1.id,
                complaint_id_2=c2.id,
                relationship_type=rel_type,
                similarity_score=score,
                matching_reasons=json.dumps(reasons),
                review_status=r_status,
                lead_bureau_id=bureaus["REG"].id,
            )
            db.add(rc)
            db.flush()

            # Seed coordination room messages
            db.add(CoordinationMessage(
                related_case_id=rc.id,
                officer_id=user_objects["sharma@samanvay.demo"].id,
                body="Identified overlapping regulatory inquiry on this college. Regulation Bureau proposing lead under approval violation mandate.",
                mentions=json.dumps(["Sunita Verma"]),
            ))
            db.add(CoordinationMessage(
                related_case_id=rc.id,
                officer_id=user_objects["verma@samanvay.demo"].id,
                body="Agreed. PGRC concurs with Regulation Bureau lead. We will coordinate joint show-cause hearings.",
                mentions=json.dumps(["R.K. Sharma"]),
            ))

        # Add Action Intent for the conflict pair (Institute of Chemical Technology hearing 8 Nov vs inspection 9 Nov)
        hearing_date = date(today.year, 11, 8)
        inspection_date = date(today.year, 11, 9)

        db.add(ActionIntent(
            complaint_id=c_conf_pgrc.id,
            institution_id=coll_conflict.id,
            officer_id=user_objects["verma@samanvay.demo"].id,
            bureau_id=bureaus["PGRC"].id,
            intent_type=IntentType.HEARING,
            planned_date=hearing_date,
            status=IntentStatus.PROPOSED,
            conflicts_json=json.dumps([f"Regulation Bureau surprise inspection scheduled for {inspection_date.strftime('%d %b')}; potential conflicting college directives."]),
        ))
        db.add(ActionIntent(
            complaint_id=c_conf_rb.id,
            institution_id=coll_conflict.id,
            officer_id=user_objects["sharma@samanvay.demo"].id,
            bureau_id=bureaus["REG"].id,
            intent_type=IntentType.INSPECTION,
            planned_date=inspection_date,
            status=IntentStatus.PROPOSED,
            conflicts_json=json.dumps([f"PGRC personal hearing scheduled for {hearing_date.strftime('%d %b')} (1 day prior); uncoordinated inspection risks prejudice to proceedings."]),
        ))

        # Add 30 additional related cases to reach 35+ total
        for _ in range(35):
            c_a, c_b = random.sample(complaints[10:], 2)
            pair = tuple(sorted([str(c_a.id), str(c_b.id)]))
            if pair in seen_overlap_pairs:
                continue
            seen_overlap_pairs.add(pair)
            same_inst = c_a.institution_id == c_b.institution_id
            diff_bur = c_a.assigned_bureau_id != c_b.assigned_bureau_id
            rel = RelationshipType.CROSS_BUREAU_COORDINATION if (same_inst and diff_bur) else (RelationshipType.RELATED_MATTER if same_inst else RelationshipType.POTENTIAL_DUPLICATE)
            score = round(random.uniform(0.68, 0.92), 3)
            reasons = ["Shared subject category: " + c_a.category]
            if same_inst:
                reasons.append("Same institution AICTE record")
            if diff_bur:
                reasons.append("Different holding bureaus requiring coordination")
            rc = RelatedCase(
                complaint_id_1=c_a.id,
                complaint_id_2=c_b.id,
                relationship_type=rel,
                similarity_score=score,
                matching_reasons=json.dumps(reasons),
                review_status=random.choice([ReviewStatus.SUGGESTED, ReviewStatus.CONFIRMED_RELATED]),
                lead_bureau_id=c_a.assigned_bureau_id,
            )
            db.add(rc)

        db.commit()
        print("Planted overlaps and Coordination Rooms successfully configured.")

        print("[8/8] Building 2,150+ Tamper-evident Hash-Chained Audit Logs...")
        # Pre-seed realistic system actions in cryptographic chain
        all_users = list(user_objects.values())
        actions = [
            ("LOGIN", "User", lambda u, c: (u.id, {"ip": f"10.0.1.{random.randint(10, 99)}"})),
            ("VIEW", "Complaint", lambda u, c: (c.id, {"case_number": c.complaint_number})),
            ("UPDATE_STATUS", "Complaint", lambda u, c: (c.id, {"status": c.current_status.value})),
            ("PROPOSE_INTENT", "ActionIntent", lambda u, c: (c.id, {"intent": "HEARING"})),
            ("VERIFY_OVERLAP", "RelatedCase", lambda u, c: (str(uuid.uuid4()), {"verdict": "CONFIRMED"})),
        ]

        prev_h = GENESIS_HASH
        base_time = datetime.utcnow() - timedelta(days=90)

        # Batch insert for high performance
        log_objects = []
        for idx in range(2150):
            actor = random.choice(all_users)
            complaint_sample = random.choice(complaints)
            act_name, ent_type, meta_fn = random.choice(actions)
            ent_id, metadata = meta_fn(actor, complaint_sample)
            ip = f"10.0.{random.randint(1, 4)}.{random.randint(2, 250)}"

            step_time = base_time + timedelta(minutes=idx * 60 + random.randint(1, 45))
            meta_str = json.dumps(metadata, sort_keys=True)
            actor_id_str = str(actor.id)

            content = f"{prev_h}|{actor_id_str}|{act_name}|{ent_type}|{ent_id or ''}|{step_time.isoformat()}|{meta_str}"
            curr_h = hashlib.sha256(content.encode()).hexdigest()

            entry = AuditLog(
                actor_user_id=actor.id,
                action=act_name,
                entity_type=ent_type,
                entity_id=str(ent_id) if ent_id else None,
                ip_address=ip,
                sanitized_metadata=meta_str,
                prev_hash=prev_h,
                hash=curr_h,
                timestamp=step_time,
            )
            log_objects.append(entry)
            prev_h = curr_h

            if len(log_objects) >= 500:
                db.bulk_save_objects(log_objects)
                db.flush()
                log_objects.clear()

        if log_objects:
            db.bulk_save_objects(log_objects)
            db.flush()

        db.commit()

        # Quick validation of audit chain
        from app.utils.helpers import verify_audit_log_integrity
        audit_check = verify_audit_log_integrity(db)
        print(f"Audit chain verification: {audit_check}")

        print("=" * 70)
        print("SEEDING COMPLETE!")
        print(f"Bureaus: {len(bureaus)}")
        print(f"Users: {len(user_objects)} (Key users: sharma@samanvay.demo, verma@samanvay.demo, patel@samanvay.demo, rao@samanvay.demo, auditor@samanvay.demo)")
        print(f"Institutions: {len(institutions)} (Showcase: ABC Institute of Technology, AICTE ID: 1-1092837465)")
        print(f"Complaints: {len(complaints)}")
        print(f"Audit Logs: 2,150 records, Chain Verified: {audit_check['verified']}")
        print("=" * 70)

    except Exception as exc:
        db.rollback()
        print(f"ERROR during seeding: {exc}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
