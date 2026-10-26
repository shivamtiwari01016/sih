# Setup Guide

## Prerequisites
- Python 3.8+
- Node.js 18+
- Optional: Docker and Docker Compose
- Optional: PostgreSQL 14+ (the default local setup uses SQLite)

## Installation

### Option 1: Local Development (SQLite, recommended)

#### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Tables are created automatically on startup.

#### Seed demo data
From the repository root, in a new terminal:
```bash
python3 scripts/seed_demo_data.py
```

The seed creates 4 bureaus, 6 users, 156 curated institutions (all 23 IITs plus
133 Maharashtra institutions), 200 complaints and overlap/coordination demo
rows. To add the catalog to an existing database without deleting anything:
```bash
python3 scripts/import_institution_catalog.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

Vite proxies `/api` to `http://localhost:8000`; override with
`VITE_API_BASE_URL` if needed.

### Option 2: Docker

1. Navigate to project directory
```bash
cd aicte-complaint-intelligence
```

2. Create environment file
```bash
cp .env.example .env
```

3. Start services
```bash
docker-compose up --build -d
```

4. Seed demo data
```bash
docker-compose exec backend python /app/scripts/seed_demo_data.py
```

The app creates tables on startup. Migrations are optional for the local SQLite
setup and available for PostgreSQL:
```bash
docker-compose exec backend alembic upgrade head
```

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Super Admin | admin@civicresolve.demo | DemoPass123! |
| Bureau Admin (Regulation) | regadmin@civicresolve.demo | DemoPass123! |
| Bureau Admin (PGRC) | pgrcadmin@civicresolve.demo | DemoPass123! |
| Case Officer | officer1@civicresolve.demo | DemoPass123! |
| Regional Officer | regional@civicresolve.demo | DemoPass123! |
| Senior Management | mgmt@civicresolve.demo | DemoPass123! |

## Testing

Backend API integration tests (isolated SQLite database):
```bash
cd backend
python3 -m pytest tests/ -v
```

Frontend production build:
```bash
cd frontend
npm run build
```

Optional headless UI smoke test, with both servers running:
```bash
python3 scripts/ui_smoke_test.py
python3 scripts/seed_demo_data.py   # reset the rows created by the test
```

## Notes
- This is a DEMO environment with synthetic complaint data
- The institution catalog is curated (23 IITs + 133 Maharashtra institutions);
  it is not the complete official AICTE/state college register
- AICTE permanent IDs are only populated from verified source data, never guessed
- Not officially affiliated with AICTE
- Never use demo credentials in production
