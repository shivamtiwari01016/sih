#!/usr/bin/env python3
"""Import the curated institution catalog without deleting existing data.

Usage (either from the repository root or from ``backend/``):

    python3 scripts/import_institution_catalog.py
    python3 scripts/import_institution_catalog.py --dry-run

The importer:
  * inserts catalog institutions that are not already present;
  * fills blank detail fields on existing institutions;
  * preserves every user-created institution, complaint and overlap;
  * recognizes the existing "lokmanya tilak clg of engineering ..." record and
    upgrades it in place so its complaints are not orphaned.

AICTE permanent IDs are never invented. Import them separately from official
AICTE data through the API or an admin import.
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if not BACKEND.is_dir():
    # Docker mounts the backend at /app and the scripts at /app/scripts.
    BACKEND = ROOT

# The default SQLite URL is relative, so imports must run from backend/ to hit
# backend/civicresolve.db. An explicitly supplied DATABASE_URL still wins.
os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT / "scripts"))

from institution_catalog import CATALOG  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.migrations import run_light_migrations  # noqa: E402
from app.models.institution import Institution  # noqa: E402

DETAIL_FIELDS = (
    "institution_type",
    "address",
    "city",
    "state",
    "region",
    "district",
    "contact_email",
    "website",
    "established_year",
    "ownership",
    "affiliation",
)

ALIASES = {
    "lokmanya tilak college of engineering": lambda name: (
        "lokmanya tilak" in name
        and ("engineering" in name or "engg" in name or "clg" in name)
    ),
}


def find_existing(db, entry):
    normalized = entry["institution_name"].lower()
    existing = (
        db.query(Institution)
        .filter(Institution.normalized_name == normalized)
        .first()
    )
    if existing:
        return existing, False

    matcher = ALIASES.get(normalized)
    if matcher:
        for candidate in db.query(Institution).all():
            if matcher((candidate.normalized_name or "").lower()):
                return candidate, True

    return None, False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would change without writing to the database",
    )
    args = parser.parse_args()

    db = SessionLocal()
    Base.metadata.create_all(bind=engine)
    run_light_migrations()
    created = 0
    updated = 0
    renamed = 0
    try:
        for entry in CATALOG:
            existing, via_alias = find_existing(db, entry)
            if existing is None:
                db.add(
                    Institution(
                        institution_name=entry["institution_name"],
                        normalized_name=entry["institution_name"].lower(),
                        institution_status="Active",
                        **{field: entry.get(field) for field in DETAIL_FIELDS},
                    )
                )
                created += 1
                continue

            changed = False
            if via_alias and existing.institution_name != entry["institution_name"]:
                existing.institution_name = entry["institution_name"]
                existing.normalized_name = entry["institution_name"].lower()
                renamed += 1
                changed = True

            for field in DETAIL_FIELDS:
                value = entry.get(field)
                if value in (None, ""):
                    continue
                current = getattr(existing, field)
                if via_alias or current in (None, ""):
                    if current != value:
                        setattr(existing, field, value)
                        changed = True

            if changed:
                updated += 1

        if args.dry_run:
            db.rollback()
        else:
            db.commit()

        print(
            f"Catalog rows: {len(CATALOG)} | created: {created} | "
            f"updated: {updated} | renamed aliases: {renamed}"
        )
        if args.dry_run:
            print("Dry run only - no changes were written.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
