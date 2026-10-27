# Samanvay (समन्वय) – Secure Complaint Coordination System for AICTE
**Smart India Hackathon PS SIH26264: "Integrated Dashboard for Monitoring and Tracking Institution-Related Complaint Cases Across AICTE Bureaus/Cells"**
*Theme: Smart Automation · Command-and-Control for Regulatory Grievances*

---

## 1. Positioning & Core Design Philosophy

AICTE complaints about the same institution reach different bureaus (Regulation Bureau RB, Public Grievance Redressal Cell PGRC, Approval Bureau, and Regional Offices). Without unified visibility, bureaus operate in silos, causing duplicate inquiries, contradictory orders, and uncoordinated inspections.

**Samanvay (समन्वय)** solves this through three core design rules:
1. **LINK cases, never merge them**: RB and PGRC operate under fundamentally distinct statutory mandates. Samanvay coordinates decisions without compromising legal jurisdictions.
2. **Minimal officer screen time — the system comes to the officer**: An exception-only "My Desk", daily 60-second briefings, pre-save duplicate banners, and one-tap conflict resolution.
3. **Strict Need-to-Know Security (ABAC)**: Multi-layer attribute-based access control (L1/L2/L3), cryptographic AES-GCM DPDP Act compliance, emergency Break-Glass protocols, and SHA-256 tamper-evident hash chaining.

---

## 2. 5-Minute Hackathon Demo Pitch (Automated Verification)

Run the single automated verification flow covering all 8 steps via the API:
```bash
python3 scripts/demo_flow.py
```

### The 8 Pitch Steps:
1. **R.K. Sharma (Regulation Bureau Officer) Logs In**: Exception-only **My Desk** opens showing urgent items, pending cross-bureau overlap requests, and prioritized SLA queue.
2. **Fast Case Intake (≤30 seconds)**: Typing "A.B.C. Inst. of Tech" autocomplete-matches "ABC Institute of Technology". **LIVE BANNER** fires before submission: *"⚠️ PGRC has an open fee case on this college (received 14 days ago, Verma). View overlap / Continue."* Sharma clicks *"Save & Open Coordination Room"*.
3. **Coordination Room**: Side-by-side comparison with diffs highlighted, 3-line summaries, and playbook lead recommendation (*Regulation Bureau* suggested based on approval norm violation rules). Sharma proposes lead.
4. **Sunita Verma (PGRC Officer) Switch**: Verma's desk receives a high-priority coordination alert. Verma clicks *"Accept Lead"*.
5. **Action Intent Conflict Warning**: Verma posts *"Hearing scheduled for 15 Nov"*. Sharma attempts to schedule *"Inspection on 16 Nov"*. Samanvay warns: *"Conflict: hearing already scheduled 15 Nov. Inspection may prejudice proceedings."* Sharma adjusts inspection to 22 Nov.
6. **One-Click Joint Decision**: Joint decision recorded: *"RB leads; PGRC conducts joint hearing on 15 Nov; RB inspection follows on 22 Nov."* Cryptographically written to **BOTH** case timelines with SHA-256 hash chaining.
7. **Dr. Ramesh Rao (Senior Management)**:
   - **Common Operating Picture (COP) Map**: Interactive Leaflet India map rendering 305+ institutions color-coded by complaint density & active cross-bureau overlaps.
   - **Coordination Health Panel**: Open overlaps down, average decision time: 4.2h, conflicts prevented count.
   - **Explainable Risk Score**: ABC Institute evaluated at 83/100 (High Risk) with full 4-factor breakdown.
8. **Chief Vigilance Auditor**:
   - Clicks *"Verify Cryptographic Chain"* -> Green shield badge: **2,188+ records verified unbroken, 0 broken, head hash logged**.
   - Review emergency **Break-Glass access** records with Sharma's/Patel's written justification and IP address.

---

## 3. Technology Stack

- **Frontend**: Next.js / React 18 + TypeScript + Tailwind CSS + Leaflet Maps + Recharts + Bilingual English/हिन्दी i18n
- **Backend**: FastAPI (Python 3.8+) + SQLAlchemy 2.0 + SQLite (development) / PostgreSQL + pgvector (production)
- **Overlap Intelligence**: 3-Layer matching engine (`rapidfuzz` token-set ratio + Hindi transliteration + `sentence-transformers` MiniLM embeddings with cosine similarity fallback)
- **Cryptography & Security**: SHA-256 blockchain-style hash chaining (`AuditLog` and `CaseAction`), Fernet/AES DPDP field encryption, TOTP MFA
- **Background Jobs**: Celery/Redis scheduled tasks + Cron SLA escalation engine

---

## 4. Evaluation Harness: Overlap Engine Accuracy

Evaluate the 3 detection layers against a ground-truth labelled benchmark:
```bash
python3 scripts/evaluate_overlap_engine.py
```

| Layer / Configuration | Precision | Recall | F1 Score | Accuracy |
| :--- | :---: | :---: | :---: | :---: |
| **Layer 1: Rules Only** (AICTE ID + Exact Category) | 100.0% | 50.0% | 66.7% | 75.0% |
| **Layer 2: Rules + Fuzzy** (Rapidfuzz + Hindi Normalization) | 100.0% | 100.0% | 100.0% | 100.0% |
| **Layer 3: Rules + Fuzzy + Semantic** (Multilingual MiniLM Embeddings) | 100.0% | 100.0% | 100.0% | 100.0% |

*(Also rendered inside the web UI at `/overlaps?tab=accuracy`).*

---

## 5. Quick Start (Run Locally)

### 1. Database Seeding
Populate the database with 305 institutions across Indian states, 650 complaints across 180 days, 40 users, and 2,150+ verified audit logs:
```bash
python3 scripts/seed_demo_data.py
```

### 2. Backend Server
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Application
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173` (or `http://localhost:3000`).

### 4. Running Integration Tests
```bash
pytest backend/tests/
```
*(All 38 API integration tests pass: 36 core + 2 institution EDA & ABAC tests).*

---

## 6. Production Deployment (Vercel & Render)

For full step-by-step instructions, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

- **Backend (Render)**:
  - Push repository to GitHub.
  - In Render, create a **New Blueprint** from [`render.yaml`](render.yaml) or a manual Python Web Service with root directory `backend`.
  - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Health check: `/health`
  - Automatic seeding: Set `AUTO_SEED=true` to automatically populate 300+ institutions and demo data on fresh instances.
- **Frontend (Vercel)**:
  - In Vercel, import repository with root directory `frontend` and preset `Vite`.
  - Add environment variable `VITE_API_BASE_URL=https://<your-render-app>.onrender.com`.
  - SPA routing rewrites and caching headers are configured in [`frontend/vercel.json`](frontend/vercel.json) and root [`vercel.json`](vercel.json).

---

## 7. Demo Accounts (Password: `DemoPass123!`)

| Role | User Name | Email | Bureau |
| :--- | :--- | :--- | :--- |
| **RB Officer** | R.K. Sharma | `sharma@samanvay.demo` | Regulation Bureau (REG) |
| **PGRC Officer** | Sunita Verma | `verma@samanvay.demo` | Public Grievance Cell (PGRC) |
| **Regional Officer** | Kirit Patel | `patel@samanvay.demo` | Regional Office (RO - West) |
| **Senior Management** | Dr. Ramesh Rao | `rao@samanvay.demo` | Member Secretary |
| **Auditor** | Chief Vigilance Auditor | `auditor@samanvay.demo` | Audit Directorate |
| **System Admin** | Administrator | `admin@samanvay.demo` | AICTE Headquarters |
