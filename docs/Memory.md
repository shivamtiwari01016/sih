# Project Memory & Session Context – Samanvay (समन्वय)

> **Purpose**: This file serves as the single source of truth for AI assistants and developers across sessions. Read this file first before making changes to avoid redundant research, regressions, or wasted tokens.
> 
> **STRICT USER DIRECTIVE**: Whenever any change, addition, bugfix, or refactoring is performed in this repository, the files in `docs/` (especially `docs/Memory.md`, and any related files like `Architecture.md`, `Rules.md`, `PRD.md`, `Phases.md`, `Design.md`) **MUST be updated immediately** in the same response turn. Never let documentation become outdated.

---

## 1. Current Live Environment State

| Component | Status | Details |
| :--- | :---: | :--- |
| **Backend Server** | **RUNNING** | `http://0.0.0.0:8000` (FastAPI / Uvicorn with auto-reload). |
| **Frontend Server** | **RUNNING** | `http://localhost:3000` (Vite 5 Dev Server, proxies `/api` to 8000). |
| **API Documentation** | **RUNNING** | `http://localhost:8000/docs` (Interactive OpenAPI / Swagger). |
| **Database File** | **SEEDED** | `d:\sih\backend\civicresolve.db` (SQLite 3). |
| **Python Virtualenv** | **ACTIVE** | `d:\sih\.venv` (Python 3.11.0, PyTorch, SentenceTransformers). |
| **Test Suite** | **PASSING** | 36 of 36 integration tests passing (`pytest backend/tests/`). |

---

## 2. Seeded Database Snapshot

Generated via `python scripts/seed_demo_data.py`:
- **Bureaus**: 4 (`REG` - Regulation, `PGRC` - Public Grievance, `APPROVAL` - Approval, `RO` - Regional Office West).
- **Users**: 40 accounts across all ABAC roles.
- **Institutions**: 305 technical colleges with coordinates, verified AICTE IDs, and aliases.
  - Showcase college: *"ABC Institute of Technology"* (AICTE ID: `1-1092837465`).
- **Complaints**: 646 realistic complaints with 180-day aging, SLA deadlines, and planted cross-bureau overlaps.
- **Audit Ledger**: 2,150 cryptographically chained SHA-256 records (Chain Verified: **TRUE**).

---

## 3. Demo Credentials (Password: `DemoPass123!`)

| User | Email | Role | Notes |
| :--- | :--- | :--- | :--- |
| **R.K. Sharma** | `sharma@samanvay.demo` | Regulation Bureau Officer | Case intake, live overlap banner, proposes coordination lead. |
| **Sunita Verma** | `verma@samanvay.demo` | PGRC Officer | Accepts lead, schedules hearing, triggers action conflict. |
| **Kirit Patel** | `patel@samanvay.demo` | Regional Officer (West) | Field inspections, local college compliance. |
| **Dr. Ramesh Rao** | `rao@samanvay.demo` | Member Secretary / Mgmt | National Common Operating Picture map, college risk scores. |
| **Chief Auditor** | `auditor@samanvay.demo` | Vigilance Auditor | 1-Click SHA-256 cryptographic chain check, Break-Glass logs. |
| **Administrator** | `admin@samanvay.demo` | Super Admin | System parameters, bureau definitions, user provisioning. |

---

## 4. Key Fixes & Hard-Won Learnings (Do Not Regress)

### 1. SQLite UUID Dialect Compatibility
- **Issue**: Models used `from sqlalchemy.dialects.postgresql import UUID`, which throws `UnsupportedCompilationError` on SQLite.
- **Solution**: Added `@compiles(UUID, "sqlite")` in [database.py](file:///d:/sih/backend/app/core/database.py) to render as `CHAR(36)`. Never remove this hook.

### 2. Passlib & Bcrypt 4.1.x Incompatibility
- **Issue**: `bcrypt >= 4.1.0` removed `__about__.__version__`, triggering trapped stack traces in Passlib.
- **Solution**: Pinned `bcrypt==4.0.1` in the virtual environment.

### 3. Windows Unicode Console Encoding
- **Issue**: Printing Hindi characters (e.g., *समन्वय*) on Windows default console (cp1252) caused `UnicodeEncodeError`.
- **Solution**: Added `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` in [seed_demo_data.py](file:///d:/sih/scripts/seed_demo_data.py). Keep this in all standalone scripts.

### 4. Cross-Platform Test DB Path
- **Issue**: [conftest.py](file:///d:/sih/backend/tests/conftest.py) hardcoded `/tmp/opencode/...`, failing on Windows.
- **Solution**: Updated to `os.path.join(tempfile.gettempdir(), "civicresolve_test.db").replace("\\", "/")`.

### 5. Overlaps Accuracy Response Structure
- **Issue**: Frontend `Overlaps.tsx` expected `{ results: [...] }` array, while backend `/api/overlaps/accuracy` returned `{ metrics: { ... } }` dictionary, causing `Cannot read properties of undefined (reading 'map')`.
- **Solution**: 
  - Aligned backend endpoint in [overlaps.py](file:///d:/sih/backend/app/api/v1/endpoints/overlaps.py) to return both `results` array and `metrics` dictionary.
  - Added normalization and safe optional chaining `(accuracyData.results || []).map(...)` in [Overlaps.tsx](file:///d:/sih/frontend/src/pages/Overlaps.tsx).

---

## 5. Verification Commands

Run these to verify system health at any point:

```bash
# 1. Run all backend tests
d:\sih\.venv\Scripts\pytest.exe backend/tests/

# 2. Re-seed demo database
d:\sih\.venv\Scripts\python.exe scripts/seed_demo_data.py

# 3. Run automated 8-step demo pitch flow
d:\sih\.venv\Scripts\python.exe scripts/demo_flow.py

# 4. Check backend health endpoint
curl http://localhost:8000/health
```
