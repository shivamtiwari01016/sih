# Coding Rules & AI Agent Constraints – Samanvay (समन्वय)

This document establishes development conventions, library constraints, error-handling protocols, and behavioral rules for any developer or AI coding assistant working on Project Samanvay.

---

## 1. Approved & Prohibited Technologies

### 1.1 Backend (Python 3.11 / FastAPI)
- **Approved**:
  - `fastapi`, `uvicorn`, `pydantic` (v2), `pydantic-settings`
  - `sqlalchemy` (v2.0 syntax: `select()`, `db.scalars()`, `declarative_base()`)
  - `rapidfuzz` for phonetic and fuzzy string normalization
  - `sentence-transformers` (`all-MiniLM-L6-v2`) with try/except fallback for semantic vectors
  - `cryptography` (Fernet) for DPDP Act field-level encryption
  - `pytest` & `pytest-asyncio` for unit and integration testing
  - `bcrypt` pinned to `4.0.1` (to prevent Passlib `__about__` attribute deprecation errors)
- **Prohibited**:
  - **DO NOT** use Django or Flask components.
  - **DO NOT** introduce raw SQL queries that bypass SQLAlchemy parameterized statements (risk of SQL injection).
  - **DO NOT** hardcode Unix-only paths like `/tmp/...` (always use `tempfile.gettempdir()` for Windows and cross-platform compatibility).
  - **DO NOT** assume PostgreSQL in local development (must maintain SQLite compatibility with `@compiles(UUID, "sqlite")`).

### 1.2 Frontend (React 18 / TypeScript / Vite)
- **Approved**:
  - React 18 functional components with standard hooks (`useState`, `useEffect`, `useCallback`, `useMemo`)
  - Tailwind CSS with predefined semantic classes
  - `@tanstack/react-query` for server state management
  - `lucide-react` for iconography
  - `leaflet` & `@types/leaflet` for geographic mapping
  - `recharts` for charts and metrics visualization
  - `sonner` or Radix Toast for notifications
- **Prohibited**:
  - **DO NOT** use arbitrary CSS-in-JS libraries (e.g. styled-components or emotion).
  - **DO NOT** use class-based React components.
  - **DO NOT** use `any` type in TypeScript where proper interfaces can be defined.
  - **DO NOT** make unauthenticated API requests directly bypassing `api.ts` Axios instance.

---

## 2. Core Architectural & Domain Rules

1. **Never Merge Cases**:
   - The system must **NEVER** expose a database mutation that deletes a case in favor of another or merges rows.
   - Cross-bureau relationships must strictly be recorded via the `RelatedCase` linkage table and coordinated through the `CoordinationDecision` and `ActionIntent` workflows.
2. **Preserve DPDP Act Masking**:
   - Complainant PII must never be returned in plain text to unauthorized bureaus or in global search results.
   - PII fields must pass through `decrypt_pii()` only when the requesting user possesses valid Bureau/L2 permissions or an approved Break-Glass emergency token.
3. **Audit Log Immutability**:
   - Every state change in a complaint (`status`, `assigned_officer`, `disposal_notes`) must write an entry to `CaseAction` and `AuditLog`.
   - The SHA-256 hash must incorporate the previous record's hash to preserve chain continuity.
   - Never update or delete rows from `audit_logs` or `case_actions`.

---

## 3. Error Handling & API Responses

1. **HTTP Status Codes**:
   - `200 OK`: Successful fetch or non-creation mutations.
   - `201 Created`: Successful creation of complaints, users, institutions.
   - `400 Bad Request`: Validation failure or business constraint violation (e.g., date in past).
   - `401 Unauthorized`: Missing or expired JWT token.
   - `403 Forbidden`: Insufficient ABAC privileges (e.g., officer attempting cross-bureau write).
   - `404 Not Found`: Entity not found.
   - `409 Conflict`: Action Intent scheduling collision or duplicate case attempt.
2. **Consistent JSON Error Format**:
   ```json
   {
     "detail": "Descriptive, human-readable error message"
   }
   ```
3. **Frontend Defensive Rendering**:
   - Always use optional chaining on array/object responses (e.g., `(data?.results || []).map(...)`).
   - Wrap remote API calls in `try/catch` blocks with user-facing toast notifications.
   - Provide clean empty states (`EmptyState` component) and loading spinners (`LoadingBlock`).

---

## 4. AI Agent Behavioral Rules

1. **Preserve Comments & Docstrings**: Never strip existing architectural notes, comments, or bilingual strings unless instructed.
2. **Validate Before Concluding**: Always run `pytest backend/tests/` to confirm that changes have not broken existing integration tests.
3. **No Placeholders in Code**: Do not output `// TODO: implement later` or dummy mock handlers for core functionality.
4. **Console Output Encoding**: When writing Python scripts for Windows, ensure UTF-8 encoding support via `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` so Devanagari characters (e.g., समन्वय) do not trigger `UnicodeEncodeError`.
5. **Mandatory Documentation Synchronization (Strict)**: Whenever ANY change, bugfix, new feature, dependency update, or schema alteration is made in the project, the corresponding files in `docs/` (specifically `docs/Memory.md`, and if relevant `PRD.md`, `Architecture.md`, `Rules.md`, `Phases.md`, `Design.md`) MUST be updated in the same turn to ensure documentation never goes stale.
