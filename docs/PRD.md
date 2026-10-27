# Project Requirements Document (PRD) – Samanvay (समन्वय)

**Smart India Hackathon Problem Statement SIH26264**  
*Integrated Dashboard for Monitoring and Tracking Institution-Related Complaint Cases Across AICTE Bureaus/Cells*

---

## 1. Problem Definition & Objectives

### 1.1 The Problem
AICTE receives thousands of complaints every year concerning technical education institutions across India. These complaints land across different organizational silos:
- **Regulation Bureau (RB)**: Deals with statutory violations, teacher-student ratios, land norms, and unapproved seat expansions.
- **Public Grievance Redressal Cell (PGRC)**: Handles citizen and student grievances regarding fee extortion, withholding of original certificates, harassment, and refund denial.
- **Approval Bureau**: Handles annual Extension of Approval (EoA) and accreditation status.
- **Regional Offices (RO)**: Carry out physical verifications and surprise spot checks.

Historically, bureaus operated without visibility into each other's cases. This led to:
1. **Duplicate Inquiries**: Two separate inquiry committees summoned college officials on overlapping dates.
2. **Contradictory Orders**: One bureau granted relief while another recommended punitive action.
3. **Delayed Dispute Resolution**: Complaints lingered beyond SLA targets due to cross-bureau ping-ponging.

### 1.2 Core Objective
To build **Samanvay (समन्वय)**: A real-time, secure, cross-bureau coordination and tracking platform that enables AICTE bureaus to detect overlaps, synchronize proceedings, and arrive at joint decisions without compromising independent legal jurisdictions.

---

## 2. Target Users & Personas

| Persona | Role / Designation | Core Responsibilities & Needs |
| :--- | :--- | :--- |
| **Case Officer** (e.g., R.K. Sharma - RB, Sunita Verma - PGRC) | Level-1 / Level-2 Bureau Officer | Needs minimal screen time, daily morning briefing, pre-save duplicate warnings, fast case logging, and coordination chat. |
| **Bureau Administrator** | Bureau Head (Director / Joint Director) | Assigns cases, approves inter-bureau transfers, monitors bureau SLA compliance, signs joint decisions. |
| **Regional Officer** (e.g., Kirit Patel - RO West) | Field Inspector / Regional Director | Schedules physical inspections, submits field reports, monitors regional institutional compliance. |
| **Senior Management** (e.g., Dr. Ramesh Rao - Member Secretary) | Executive Leadership (Chairman / Vice Chairman / MS) | Needs macro-level Common Operating Picture (COP), institutional composite risk ranking, and national health analytics. |
| **Chief Vigilance Auditor** | Vigilance & Compliance Auditor | Independent integrity verification: checks cryptographic hash chains, monitors emergency Break-Glass access logs. |
| **Super Administrator** | IT / Systems Administrator | Provisions users, configures ABAC roles, tunes similarity thresholds, manages bureau definitions. |

---

## 3. Product Principles (Non-Negotiable)

1. **LINK Cases, Never Merge Them**:
   - RB and PGRC have fundamentally different statutory mandates. Merging cases destroys legal standing in court proceedings. Samanvay links cases under a shared Coordination Room.
2. **The System Comes to the Officer**:
   - Officers should not spend hours clicking through dashboards. The system provides:
     - **My Desk**: Exception-only view (urgent deadlines, incoming coordination requests, active conflicts).
     - **Pre-Save Live Overlap Banner**: Proactive duplicate warnings within $\le$ 30 seconds *before* submission.
     - **Action Intent Conflict Warnings**: Proactive detection of scheduling clashes.
3. **Strict Need-to-Know Security (ABAC + DPDP Act Compliance)**:
   - Sensitive whistleblower and POSH complaints are masked across bureaus.
   - PII is field-level encrypted (AES-GCM / Fernet).
   - Emergency cross-bureau access requires written Break-Glass justification and audit logging.

---

## 4. Key Functional Requirements & Features

### 4.1 Case Intake & Pre-Check Overlap Intelligence
- **F-1.1 Fuzzy Institution Autocomplete**: As user types a college name, matches against 305+ curated institutions and alternate abbreviations/aliases.
- **F-1.2 Live Pre-Save Banner**: Debounced background check triggers before form submission; displays a yellow warning card if an active case exists in another bureau.
- **F-1.3 Fast Case Registration**: Allows one-tap "Save & Open Coordination Room" or standard intake under 30 seconds.

### 4.2 Overlap Detection Engine
- **F-2.1 Layer 1 (Rules)**: Matches exact AICTE Permanent ID and identical grievance category.
- **F-2.2 Layer 2 (Fuzzy & Phonetics)**: `rapidfuzz` token-set ratio + Hindi transliteration normalization to match institutional aliases.
- **F-2.3 Layer 3 (Semantic Similarity)**: Cosine similarity over vector embeddings (`all-MiniLM-L6-v2`) on complaint narratives.
- **F-2.4 Accuracy Evaluation Benchmark**: Embedded evaluation harness testing the engine against 120 labelled ground-truth pairs.

### 4.3 Coordination Room
- **F-3.1 Side-by-Side Diff View**: Direct comparison of overlapping cases (dates, allegations, status, evidence).
- **F-3.2 Playbook Lead Recommendation**: Automatically proposes lead bureau based on statutory gravity (e.g., EoA violation $\rightarrow$ Regulation Bureau leads).
- **F-3.3 Cross-Bureau Timeline & Chat**: Immutable, timestamped inter-bureau messaging.
- **F-3.4 One-Click Joint Decision**: Cryptographically records binding joint decision to both case files simultaneously.

### 4.4 Action Intent Conflict Engine
- **F-4.1 Intent Declaration**: Officers declare intended high-impact events (Hearings, Surprise Inspections, Show Cause Notices).
- **F-4.2 Temporal Conflict Detection**: Warns if an inspection is scheduled within 7 days of an existing hearing date.
- **F-4.3 Conflict Resolution**: Provides options to reschedule or harmonize timelines.

### 4.5 Executive Common Operating Picture (COP)
- **F-5.1 Interactive Leaflet Map**: Visualizes institutions across India color-coded by complaint density and active overlaps.
- **F-5.2 Institutional Risk Scoring**: 0–100 composite risk score with 4-factor breakdown (Volume, Severity, Overlaps, SLA breach).

### 4.6 Cryptographic Audit Ledger & Compliance
- **F-6.1 SHA-256 Hash Chaining**: Every action and audit log entry points to the previous record's SHA-256 hash.
- **F-6.2 One-Click Chain Verification**: Verifies unbroken integrity across 2,150+ audit records.
- **F-6.3 Break-Glass Protocol**: Emergency access request with mandatory written justification and IP tracking.

---

## 5. Non-Functional Requirements

- **Performance**: API responses $\le$ 200ms; fuzzy autocomplete $\le$ 50ms; overlap scan under 2 seconds.
- **Security**: OAuth2 Bearer JWT authentication, DPDP-compliant field encryption, bcrypt password hashing.
- **Availability & Portability**: Dual database support (SQLite for instant zero-dependency local dev, PostgreSQL + pgvector for production).
- **Accessibility & Localization**: Full English and हिन्दी bilingual interface toggle.
