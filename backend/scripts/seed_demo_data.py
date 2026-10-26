#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/app')

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash
from app.models import *
from datetime import date, timedelta
from faker import Faker
import random

fake = Faker()
Faker.seed(12345)
random.seed(12345)

def seed_data():
    db = SessionLocal()
    
    try:
        print("Clearing existing data...")
        db.query(AuditLog).delete()
        db.query(Notification).delete()
        db.query(Document).delete()
        db.query(BureauTransfer).delete()
        db.query(RelatedCase).delete()
        db.query(CaseAction).delete()
        db.query(Complaint).delete()
        db.query(User).delete()
        db.query(Institution).delete()
        db.query(Bureau).delete()
        db.commit()
        
        print("Creating Bureaus...")
        bureaus_data = [
            {"code": "REG", "name": "Regulation Bureau", "desc": "Handles regulatory compliance complaints"},
            {"code": "PGRC", "name": "Public Grievance Redressal Cell", "desc": "Handles public grievances"},
            {"code": "EAP", "name": "Approval Process Bureau (Illustrative)", "desc": "Illustrative - handles approval related matters"},
            {"code": "RO", "name": "Regional Office (Illustrative)", "desc": "Illustrative - handles regional matters"},
        ]
        bureaus = []
        for b in bureaus_data:
            bureau = Bureau(bureau_code=b["code"], bureau_name=b["name"], description=b["desc"])
            db.add(bureau)
            bureaus.append(bureau)
        db.commit()
        
        print("Creating Users...")
        users_data = [
            {"name": "System Admin", "email": "admin@civicresolve.demo", "role": UserRole.SUPER_ADMIN, "bureau": None},
            {"name": "Regulation Admin", "email": "regadmin@civicresolve.demo", "role": UserRole.BUREAU_ADMIN, "bureau": bureaus[0]},
            {"name": "PGRC Admin", "email": "pgrcadmin@civicresolve.demo", "role": UserRole.BUREAU_ADMIN, "bureau": bureaus[1]},
            {"name": "Case Officer 1", "email": "officer1@civicresolve.demo", "role": UserRole.CASE_OFFICER, "bureau": bureaus[0]},
            {"name": "Regional Officer", "email": "regional@civicresolve.demo", "role": UserRole.REGIONAL_OFFICER, "bureau": bureaus[3]},
            {"name": "Senior Management", "email": "mgmt@civicresolve.demo", "role": UserRole.SENIOR_MANAGEMENT, "bureau": None},
        ]
        for u in users_data:
            user = User(
                full_name=u["name"],
                email=u["email"],
                password_hash=get_password_hash("DemoPass123!"),
                role=u["role"],
                bureau_id=u["bureau"].id if u["bureau"] else None,
                active=True
            )
            db.add(user)
        db.commit()
        
        print("Creating Institutions...")
        institutions_names = [
            "Western Valley Institute of Technology",
            "Horizon College of Engineering",
            "Greenfield Technical University",
            "Coastal Institute of Applied Sciences",
            "Meridian Polytechnic College",
            "Sunrise Institute of Management",
            "Blue Ridge Engineering College",
            "Riverdale Technical Institute",
            "Mountain View College of Technology",
            "Lakeside Polytechnic",
        ]
        institutions = []
        for i, name in enumerate(institutions_names * 5):  # 50 institutions
            inst = Institution(
                institution_name=f"{name} - Campus {i%5+1}" if i >= 10 else name,
                normalized_name=f"{name.lower()} campus {i%5+1}" if i >= 10 else name.lower(),
                aicte_permanent_id=f"AICTE-{100000 + i}",
                institution_type=random.choice(["Engineering", "Polytechnic", "Management", "University"]),
                address=fake.street_address(),
                city=fake.city(),
                state=random.choice(["Maharashtra", "Karnataka", "Tamil Nadu", "Delhi", "Uttar Pradesh"]),
                region=random.choice(["West", "South", "North", "East"]),
                district=fake.city(),
                institution_status="Active"
            )
            db.add(inst)
            institutions.append(inst)
        db.commit()
        
        print("Creating Complaints...")
        categories = ["Faculty Related", "Infrastructure", "Fee Structure", "Admission", "Examination", "Affiliation"]
        statuses = [ComplaintStatus.RECEIVED, ComplaintStatus.UNDER_SCRUTINY, ComplaintStatus.UNDER_PROCESS, 
                   ComplaintStatus.AWAITING_INFORMATION, ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED]
        priorities = [Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.URGENT]
        
        complaints = []
        for i in range(200):
            inst = random.choice(institutions)
            bureau = random.choice(bureaus)
            received = date.today() - timedelta(days=random.randint(1, 120))
            expected = received + timedelta(days=random.randint(15, 60))
            status = random.choice(statuses)
            disposed = received + timedelta(days=random.randint(10, 50)) if status in [ComplaintStatus.DISPOSED, ComplaintStatus.CLOSED] else None
            
            complaint = Complaint(
                complaint_number=f"CR-{2026}-{i+1:06d}",
                institution_id=inst.id,
                received_date=received,
                source_channel=random.choice(["Online Portal", "Email", "Letter", "Phone"]),
                category=random.choice(categories),
                subject=f"Complaint regarding {random.choice(['faculty', 'infrastructure', 'fees', 'admission'])} issues",
                description=fake.text(max_nb_chars=500),
                priority=random.choice(priorities),
                current_status=status,
                assigned_bureau_id=bureau.id,
                expected_disposal_date=expected,
                disposed_at=disposed
            )
            db.add(complaint)
            complaints.append(complaint)
        db.commit()
        
        # Create some related complaint pairs for demonstration
        print("Creating overlap suggestions...")
        if len(complaints) >= 2:
            # Create a pair with same institution
            c1 = complaints[0]
            c2 = complaints[1]
            if c1.institution_id == c2.institution_id:
                related = RelatedCase(
                    complaint_id_1=c1.id,
                    complaint_id_2=c2.id,
                    relationship_type=RelationshipType.RELATED_MATTER,
                    similarity_score=0.75,
                    matching_reasons='["Same institution", "Similar category"]',
                    review_status=ReviewStatus.SUGGESTED
                )
                db.add(related)
            else:
                # Make same institution
                c2.institution_id = c1.institution_id
                related = RelatedCase(
                    complaint_id_1=c1.id,
                    complaint_id_2=c2.id,
                    relationship_type=RelationshipType.CROSS_BUREAU_COORDINATION,
                    similarity_score=0.82,
                    matching_reasons='["Same verified institution", "Cases assigned to different Bureaus", "Description similarity"]',
                    review_status=ReviewStatus.SUGGESTED
                )
                db.add(related)
            db.commit()
        
        print("Seeding completed successfully!")
        print(f"Created: {len(bureaus)} bureaus, {len(users_data)} users, {len(institutions)} institutions, {len(complaints)} complaints")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
