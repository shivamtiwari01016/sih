"""Idempotent schema upgrades for local development and demo databases."""
from sqlalchemy import inspect, text
from app.core.database import engine, Base


TABLE_MIGRATIONS = {
    "institutions": [
        ("website", "VARCHAR"),
        ("established_year", "INTEGER"),
        ("ownership", "VARCHAR"),
        ("affiliation", "VARCHAR"),
        ("aliases", "TEXT"),
        ("lat", "FLOAT"),
        ("lng", "FLOAT"),
        ("embedding", "TEXT"),
    ],
    "users": [
        ("mfa_enabled", "BOOLEAN DEFAULT 0"),
        ("mfa_secret", "VARCHAR"),
    ],
    "complaints": [
        ("complainant_pseudo_id", "VARCHAR"),
        ("complainant_encrypted", "TEXT"),
        ("sensitivity", "VARCHAR DEFAULT 'Normal'"),
        ("summary", "TEXT"),
        ("language", "VARCHAR DEFAULT 'en'"),
        ("embedding_json", "TEXT"),
    ],
    "case_actions": [
        ("prev_hash", "VARCHAR"),
        ("hash", "VARCHAR"),
    ],
    "audit_logs": [
        ("ip_address", "VARCHAR"),
        ("prev_hash", "VARCHAR"),
        ("hash", "VARCHAR"),
    ],
    "related_cases": [
        ("lead_bureau_id", "VARCHAR"),
        ("lead_bureau_code", "VARCHAR"),
        ("ack_due_at", "TIMESTAMP"),
    ],
}


def run_light_migrations() -> None:
    # First, create any completely new tables (action_intents, coordination_messages, etc.)
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table_name, columns in TABLE_MIGRATIONS.items():
            if table_name not in existing_tables:
                continue
            existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
            for col_name, col_type in columns:
                if col_name not in existing_cols:
                    try:
                        connection.execute(
                            text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                        )
                    except Exception as e:
                        # SQLite or PostgreSQL might have slight syntax nuance; ignore if already exists
                        pass
