# Project Implementation Phases & Milestones – Samanvay (समन्वय)

This document outlines the step-by-step roadmap followed during the development of Samanvay and highlights completed phases along with future post-hackathon extensions.

---

## Phase Breakdown Matrix

```
[Phase 1: Foundation] ────► [Phase 2: Overlap Engine] ────► [Phase 3: Coordination Room]
                                                                     │
[Phase 6: Pitch & Demo] ◄── [Phase 5: Executive COP] ◄─── [Phase 4: Security & DPDP]
```

---

## Phase 1: Foundation & Data Architecture (Completed ✓)
- **Goal**: Set up cross-platform backend and frontend skeletons, relational models, and seeding scripts.
- **Key Deliverables**:
  1. FastAPI project structure with SQLAlchemy 2.0 ORM.
  2. 16 Core relational models with cross-platform SQLite/Postgres UUID dialect compiler.
  3. Curated catalog of 305+ technical colleges across Indian states with verified coordinates.
  4. Deterministic database seeder generating 40 users across all roles, 650 realistic complaints, and 180-day SLA distributions.
  5. Vite + React 18 + Tailwind CSS frontend boilerplate with authentication context and language switcher.

---

## Phase 2: Multi-Layer Overlap Intelligence Engine (Completed ✓)
- **Goal**: Detect duplicate complaints and institutional overlaps across bureaus using fuzzy matching and NLP embeddings.
- **Key Deliverables**:
  1. **Layer 1**: Deterministic AICTE ID and exact category matching.
  2. **Layer 2**: RapidFuzz token-set ratio + Hindi phonetic/transliteration normalization.
  3. **Layer 3**: `sentence-transformers` (`all-MiniLM-L6-v2`) semantic similarity embeddings with cosine fallback.
  4. Real-time pre-save duplicate banner in intake form (`/api/complaints/pre-check-overlap`).
  5. 120-Pair ground-truth benchmark evaluation harness ([evaluate_overlap_engine.py](file:///d:/sih/scripts/evaluate_overlap_engine.py)).

---

## Phase 3: Collaborative Coordination Room & Conflict Engine (Completed ✓)
- **Goal**: Give officers a workspace to coordinate overlapping cases without merging independent files.
- **Key Deliverables**:
  1. Side-by-side case diff modal with automated summaries and category comparisons.
  2. Statutory Playbook recommendation engine (Regulation Bureau suggested for approval violations; PGRC for student fees).
  3. Real-time cross-bureau messaging and lead acceptance workflow.
  4. **Action Intent Conflict Engine**: Checks proposed hearings vs inspections to prevent contradictory scheduling.
  5. One-click joint decision recording with dual-timeline hash linking.

---

## Phase 4: Cryptography, DPDP Act & ABAC Security (Completed ✓)
- **Goal**: Implement zero-trust security and government data compliance.
- **Key Deliverables**:
  1. **DPDP Compliance**: Fernet / AES-GCM encryption of complainant personal data.
  2. **Multi-layer ABAC**: Automatic masking of sensitive and whistleblower allegations across bureau boundaries.
  3. **Break-Glass Protocol**: Emergency access request with mandatory legal justification and audit alert.
  4. **Tamper-Evident SHA-256 Ledger**: Hash chaining across all case actions and system audit logs.
  5. One-click verification tool in Audit Logs UI calculating 2,150+ records from genesis block to head hash.

---

## Phase 5: Common Operating Picture (COP) & Executive Dashboards (Completed ✓)
- **Goal**: Provide senior AICTE leadership with national situational awareness and actionable institutional health metrics.
- **Key Deliverables**:
  1. **My Desk**: Exception-only morning view showing critical SLA deadlines, pending coordination requests, and active conflicts.
  2. **Interactive Leaflet India Map**: 305+ colleges color-coded by institutional risk score and overlap status.
  3. **4-Factor Explainable Risk Score**: Modal showing Volume, Severity, Overlap Density, and Non-cooperation breakdowns.
  4. Monthly bureau performance reports and CSV data export capabilities.

---

## Phase 6: Automated Verification & Hackathon Pitch (Completed ✓)
- **Goal**: Provide automated end-to-end verification and bulletproof live demonstration capabilities.
- **Key Deliverables**:
  1. Automated 8-step verification flow script ([demo_flow.py](file:///d:/sih/scripts/demo_flow.py)) simulating all personas in sequence.
  2. 36 Comprehensive integration tests covering all endpoints passing under `pytest`.
  3. One-click login persona switchers on the login screen.
  4. Resilient frontend error handling and cross-platform Windows compatibility.

---

## Future Roadmap (Post-Hackathon Phase 7)
- [ ] **DigiLocker / NAD Integration**: Direct verification of student degree certificates to expedite certificate-withholding grievances.
- [ ] **AICTE Portal SSO**: SAML 2.0 / OpenID Connect integration with official AICTE portals (`aicte-india.org`).
- [ ] **SMS / WhatsApp Gateway**: Automated citizen notification dispatch via government SMS gateways.
- [ ] **Multilingual Voice-to-Text Complaint Filing**: Regional language voice recognition for rural complainants.
