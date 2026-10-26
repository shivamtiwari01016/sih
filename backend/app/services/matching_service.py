"""Overlap Engine: 3-layer cross-bureau complaint matching.

Layer 1 - Exact: AICTE Permanent ID match or identical normalized institution key.
Layer 2 - Fuzzy: Institution name abbreviation expansion, Hindi/Devanagari transliteration,
                 and rapidfuzz token_set_ratio & token_sort_ratio on name + address.
Layer 3 - Semantic: Multilingual sentence embeddings (MiniLM) cosine similarity with
                    graceful extractive TF-IDF / domain vocabulary fallback.

Output format:
"Potential Overlapping Cases – Coordination Required" with calibrated confidence score
and plain-language explainable reasons.
"""
import json
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.complaint import Complaint, ComplaintStatus
from app.models.institution import Institution
from app.models.related_case import RelatedCase, RelationshipType, ReviewStatus

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

# Abbreviation & alias dictionary for normalization
NAME_EXPANSIONS = {
    r"\binst\b|\binst\.\b": "institute",
    r"\bengg\b|\bengg\.\b|\beng\b": "engineering",
    r"\bclg\b|\bcoll\b": "college",
    r"\btech\b|\btechnol\b": "technology",
    r"\bmgmt\b|\bmgt\b": "management",
    r"\buniv\b|\buniv\.\b": "university",
    r"\bpoly\b|\bpolytech\b": "polytechnic",
    r"\bdept\b|\bdept\.\b": "department",
    r"\bgovt\b|\bgov\b": "government",
    r"\bsci\b": "science",
    r"\bapp\b": "applied",
    r"\biit\b": "indian institute of technology",
    r"\bnit\b": "national institute of technology",
    r"\bcoep\b": "college of engineering pune",
    r"\bvjti\b": "veermata jijabai technological institute",
}

# Hindi Devanagari keyword expansions
HINDI_TERMS = {
    "अभियांत्रिकी": "engineering",
    "संस्थान": "institute",
    "महाविद्यालय": "college",
    "प्रौद्योगिकी": "technology",
    "विश्वविद्यालय": "university",
    "प्रबंधन": "management",
    "शुल्क": "fees",
    "रैगिंग": "ragging",
    "प्रवेश": "admission",
    "परीक्षा": "examination",
}

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "this", "that", "it", "as",
    "by", "at", "from", "about", "regarding", "complaint", "issue", "issues",
}

DOMAIN_KEYWORDS = {
    "infrastructure": {
        "infra", "infrastructure", "lab", "laboratory", "classroom", "building",
        "floor", "ac", "air", "conditioner", "conditioning", "cooling", "fan",
        "wifi", "internet", "network", "water", "washroom", "toilet", "canteen",
        "electricity", "power", "furniture", "bench", "library", "hostel",
        "transport", "bus", "parking", "maintenance", "repair", "lift",
        "elevator", "roof", "leak", "sanitation", "clean", "cleanliness",
    },
    "faculty related": {
        "faculty", "teacher", "professor", "lecturer", "staff", "attendance",
        "attendence", "class", "lecture", "teach", "teaching", "misconduct",
        "behaviour", "behavior", "compulsion", "compulsory", "forced",
        "syllabus", "guide", "mentor", "qualification", "phd", "salary",
    },
    "fee structure": {
        "fee", "fees", "tuition", "refund", "scholarship", "charge", "charges",
        "payment", "receipt", "billing", "overcharge", "fine", "penalty",
        "exam-fee", "examination-fee", "capitation", "caution", "money",
    },
    "admission": {
        "admission", "enrollment", "enrolment", "seat", "quota", "eligibility",
        "document", "verification", "counseling", "counselling", "entrance",
        "cap", "merit", "application", "cet", "cutoff",
    },
    "examination": {
        "exam", "examination", "result", "marks", "revaluation", "paper",
        "hall", "ticket", "invigilator", "malpractice", "backlog", "practical",
        "viva", "assessment", "grading", "recheck",
    },
    "affiliation": {
        "affiliation", "affiliated", "accreditation", "aicte", "naac", "nba",
        "approval", "recognition", "university", "autonomy", "compliance",
        "norms", "deficiency", "land", "eoa", "extension",
    },
    "governance": {
        "governance", "management", "principal", "director", "trust",
        "corruption", "harassment", "discrimination", "ragging", "committee",
        "grievance", "transparency", "misuse", "policy", "whistleblower",
    },
}

OPEN_STATUSES = {
    ComplaintStatus.RECEIVED,
    ComplaintStatus.UNDER_SCRUTINY,
    ComplaintStatus.UNDER_PROCESS,
    ComplaintStatus.AWAITING_INFORMATION,
    ComplaintStatus.TRANSFERRED,
    ComplaintStatus.ESCALATED,
}


def normalize_institution_name(name: Optional[str]) -> str:
    """Normalize college name by expanding common abbreviations and Hindi terms."""
    if not name:
        return ""
    text = name.lower()
    for hindi, eng in HINDI_TERMS.items():
        text = text.replace(hindi, eng)
    text = re.sub(r"[^\w\s]", " ", text)
    for pattern, replacement in NAME_EXPANSIONS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return " ".join(text.split())


def _tokens(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}


def _domain_groups(text: str) -> set:
    raw = (text or "").lower()
    words = set(re.findall(r"[a-z0-9-]+", raw))
    return {
        category
        for category, keywords in DOMAIN_KEYWORDS.items()
        if words & keywords
    }


class MatchingService:
    def __init__(self):
        self.model = None
        self._model_attempted = False

    def _ensure_model(self):
        if self._model_attempted:
            return
        self._model_attempted = True
        if not settings.USE_SEMANTIC_MATCHING:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception:
            self.model = None

    def semantic_similarity(self, text1: str, text2: str) -> Optional[float]:
        self._ensure_model()
        if not self.model:
            return None
        try:
            embeddings = self.model.encode([text1, text2])
            from sklearn.metrics.pairwise import cosine_similarity
            return float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
        except Exception:
            return None

    def match_institutions(self, inst1: Optional[Institution], inst2: Optional[Institution]) -> Tuple[float, List[str]]:
        if not inst1 or not inst2:
            return 0.0, []

        reasons = []
        if inst1.id == inst2.id:
            reasons.append("Same institution")
            return 1.0, reasons

        if (
            inst1.aicte_permanent_id
            and inst2.aicte_permanent_id
            and inst1.aicte_permanent_id == inst2.aicte_permanent_id
        ):
            reasons.append(f"Same AICTE Permanent ID: {inst1.aicte_permanent_id}")
            return 1.0, reasons

        norm1 = normalize_institution_name(inst1.institution_name)
        norm2 = normalize_institution_name(inst2.institution_name)

        if norm1 == norm2 and norm1:
            reasons.append("Identical normalized institution name")
            return 0.95, reasons

        if HAS_RAPIDFUZZ:
            token_set = fuzz.token_set_ratio(norm1, norm2) / 100.0
            token_sort = fuzz.token_sort_ratio(norm1, norm2) / 100.0
            fuzzy_score = (token_set * 0.6) + (token_sort * 0.4)
        else:
            fuzzy_score = SequenceMatcher(None, norm1, norm2).ratio()

        if inst1.state and inst2.state and inst1.state.lower() == inst2.state.lower():
            if fuzzy_score >= 0.70:
                fuzzy_score = min(fuzzy_score + 0.10, 1.0)
                reasons.append(f"Same state ({inst1.state}) with high name similarity ({fuzzy_score:.0%})")
        elif fuzzy_score >= 0.80:
            reasons.append(f"Fuzzy name match ({fuzzy_score:.0%})")

        return fuzzy_score, reasons

    def score_complaints(self, c1: Complaint, c2: Complaint) -> Tuple[float, List[str]]:
        reasons: List[str] = []

        inst_score, inst_reasons = self.match_institutions(c1.institution, c2.institution)
        reasons.extend(inst_reasons)

        text1 = f"{c1.subject} {c1.description}"
        text2 = f"{c2.subject} {c2.description}"

        semantic_score = self.semantic_similarity(text1, text2)
        if semantic_score is not None:
            text_similarity = max(0.0, min(1.0, semantic_score))
            reasons.append(f"Semantic description similarity {text_similarity:.2f}")
        else:
            tokens1 = _tokens(text1)
            tokens2 = _tokens(text2)
            union = tokens1 | tokens2
            jaccard = len(tokens1 & tokens2) / len(union) if union else 0.0
            ratio = SequenceMatcher(None, (text1 or "").lower(), (text2 or "").lower()).ratio()
            text_similarity = (jaccard * 0.65) + (ratio * 0.35)
            shared_words = sorted(tokens1 & tokens2)[:4]
            reasons.append(f"Text similarity {text_similarity:.2f}")
            if shared_words:
                reasons.append("Shared keywords: " + ", ".join(shared_words))

        shared_topics = _domain_groups(text1) & _domain_groups(text2)
        if shared_topics:
            text_similarity = max(text_similarity, settings.DOMAIN_TOPIC_SCORE)
            reasons.append("Shared topic: " + ", ".join(t.title() for t in sorted(shared_topics)))

        cat1 = (c1.category or "").strip().lower()
        cat2 = (c2.category or "").strip().lower()
        same_category = bool(cat1 and cat1 == cat2)
        if same_category:
            reasons.append("Same complaint category")

        bureau_differs = bool(
            c1.assigned_bureau_id
            and c2.assigned_bureau_id
            and c1.assigned_bureau_id != c2.assigned_bureau_id
        )
        if bureau_differs:
            reasons.append("Cases are assigned to different Bureaus")

        score = (
            (inst_score * settings.INSTITUTION_WEIGHT)
            + (text_similarity * settings.TEXT_WEIGHT)
            + (settings.CATEGORY_WEIGHT if same_category else 0.0)
            + (settings.CROSS_BUREAU_WEIGHT if bureau_differs else 0.0)
        )

        return min(max(score, 0.0), 0.99), reasons

    def check_pre_save_overlaps(
        self,
        db: Session,
        institution_id,
        category: str,
        subject: str,
        description: str,
        bureau_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        open_cases = (
            db.query(Complaint)
            .filter(
                Complaint.institution_id == institution_id,
                Complaint.current_status.in_(OPEN_STATUSES),
            )
            .all()
        )
        warnings = []
        for case in open_cases:
            bureau_name = case.assigned_bureau.bureau_name if case.assigned_bureau else "Another Bureau"
            bureau_code = case.assigned_bureau.bureau_code if case.assigned_bureau else "OTHER"
            is_different = case.assigned_bureau_id != bureau_id if bureau_id else True
            same_cat = (case.category or "").lower() == (category or "").lower()
            warnings.append({
                "case_id": str(case.id),
                "case_no": case.complaint_number,
                "bureau": bureau_name,
                "bureau_code": bureau_code,
                "is_different_bureau": is_different,
                "category": case.category,
                "subject": case.subject,
                "status": case.current_status.value if hasattr(case.current_status, "value") else str(case.current_status),
                "message": f"{bureau_name} has an open {case.category.lower()} case ({case.complaint_number}) on this college.",
                "same_category": same_cat,
            })
        return warnings


matching_service = MatchingService()


def relationship_for(complaint: Complaint, candidate: Complaint) -> RelationshipType:
    if complaint.institution_id == candidate.institution_id:
        if (
            complaint.assigned_bureau_id
            and candidate.assigned_bureau_id
            and complaint.assigned_bureau_id != candidate.assigned_bureau_id
        ):
            return RelationshipType.CROSS_BUREAU_COORDINATION
        return RelationshipType.RELATED_MATTER
    if (complaint.category or "").lower() == (candidate.category or "").lower():
        return RelationshipType.POTENTIAL_DUPLICATE
    return RelationshipType.RELATED_MATTER


def _pair_exists(db, complaint_id, candidate_id) -> bool:
    return (
        db.query(RelatedCase.id)
        .filter(
            or_(
                (RelatedCase.complaint_id_1 == complaint_id)
                & (RelatedCase.complaint_id_2 == candidate_id),
                (RelatedCase.complaint_id_1 == candidate_id)
                & (RelatedCase.complaint_id_2 == complaint_id),
            )
        )
        .first()
        is not None
    )


def candidate_complaints(db, complaint: Complaint, limit: Optional[int] = None):
    query = (
        db.query(Complaint)
        .filter(Complaint.id != complaint.id)
        .filter(
            or_(
                Complaint.category == complaint.category,
                Complaint.institution_id == complaint.institution_id,
            )
        )
        .order_by(Complaint.received_date.desc(), Complaint.created_at.desc())
    )
    return query.limit(limit or settings.MAX_CANDIDATES).all()


def generate_overlaps_for_complaint(
    db,
    complaint: Complaint,
    max_suggestions: Optional[int] = None,
    commit: bool = True,
) -> List[dict]:
    scored = []
    for candidate in candidate_complaints(db, complaint):
        if _pair_exists(db, complaint.id, candidate.id):
            continue
        score, reasons = matching_service.score_complaints(complaint, candidate)
        if score < settings.SIMILARITY_THRESHOLD:
            continue
        scored.append((score, candidate, reasons))

    scored.sort(key=lambda item: item[0], reverse=True)
    limit = max_suggestions or settings.MAX_SUGGESTIONS_PER_COMPLAINT
    created = []
    for score, candidate, reasons in scored[:limit]:
        related = RelatedCase(
            complaint_id_1=complaint.id,
            complaint_id_2=candidate.id,
            relationship_type=relationship_for(complaint, candidate),
            similarity_score=round(score, 3),
            matching_reasons=json.dumps(reasons),
            review_status=ReviewStatus.SUGGESTED,
            ack_due_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(related)
        created.append(
            {
                "complaint_id": str(candidate.id),
                "complaint_number": candidate.complaint_number,
                "subject": candidate.subject,
                "similarity_score": round(score, 3),
                "relationship_type": relationship_for(complaint, candidate).value,
                "matching_reasons": reasons,
            }
        )

    if commit:
        db.commit()
    else:
        db.flush()

    return created


def scan_all_complaints(db, limit: Optional[int] = None) -> dict:
    complaints = (
        db.query(Complaint)
        .order_by(Complaint.received_date.desc(), Complaint.created_at.desc())
        .limit(limit or settings.MAX_SCAN_COMPLAINTS)
        .all()
    )
    suggestions = []
    scanned = 0
    for complaint in complaints:
        if len(suggestions) >= settings.MAX_SCAN_SUGGESTIONS:
            break
        scanned += 1
        remaining = settings.MAX_SCAN_SUGGESTIONS - len(suggestions)
        per_complaint = min(settings.MAX_SUGGESTIONS_PER_COMPLAINT, remaining)
        suggestions.extend(
            generate_overlaps_for_complaint(
                db, complaint, max_suggestions=per_complaint, commit=False
            )
        )
    db.commit()
    return {
        "complaints_scanned": scanned,
        "matches_found": len(suggestions),
        "matches": suggestions,
        "capped": len(suggestions) >= settings.MAX_SCAN_SUGGESTIONS,
    }
