#!/usr/bin/env python3
"""Evaluation Harness for Overlap Engine Accuracy.

Generates a labelled evaluation dataset (ground-truth pairs of True Overlaps vs Non-Overlaps)
and computes Precision, Recall, and F1 Score for three configurations:
1. Rules Only (Exact AICTE ID + Category Match)
2. Rules + Fuzzy (Exact + RapidFuzz Institution Normalization)
3. Rules + Fuzzy + Semantic (Full 3-layer matching with multilingual MiniLM / TF-IDF)
"""
import json
import math
import os
import random
import sys
from typing import Any, Dict, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if not os.path.isdir(BACKEND_DIR):
    BACKEND_DIR = BASE_DIR
sys.path.insert(0, BACKEND_DIR)

from app.services.matching_service import (
    MatchingService,
    normalize_institution_name,
)

class MockInst:
    def __init__(self, id, name, aicte_id, state="Maharashtra"):
        self.id = id
        self.institution_name = name
        self.aicte_permanent_id = aicte_id
        self.state = state

class MockCase:
    def __init__(self, id, inst, category, subject, description, bureau_id):
        self.id = id
        self.institution = inst
        self.institution_id = inst.id
        self.category = category
        self.subject = subject
        self.description = description
        self.assigned_bureau_id = bureau_id
        self.current_status = "Under Process"

def generate_labelled_dataset(n_samples: int = 120) -> List[Tuple[MockCase, MockCase, bool]]:
    """Generate ground truth pairs: (CaseA, CaseB, is_overlap_label)."""
    random.seed(42)
    pairs = []

    # Overlap templates
    institutions_base = [
        ("ABC Institute of Technology", "AICTE-1001", "abc inst. of tech"),
        ("Maharashtra College of Engineering", "AICTE-1002", "maha clg of engg"),
        ("Pune Technical Institute", "AICTE-1003", "pune tech inst"),
        ("Veermata Jijabai Technological Institute", "AICTE-1004", "vjti mumbai"),
        ("National Institute of Management", "AICTE-1005", "natl inst of mgmt"),
        ("Shivaji College of Engineering & Tech", "AICTE-1006", "shivaji engg clg"),
    ]

    # Generate True Overlaps (planted pairs)
    for i in range(n_samples // 2):
        base_name, aicte_id, variant_name = institutions_base[i % len(institutions_base)]
        inst_a = MockInst(f"inst-a-{i}", base_name, aicte_id)
        # 50% have same AICTE ID, 50% have typo/abbreviation without ID match
        use_exact_id = (i % 2 == 0)
        inst_b = MockInst(f"inst-b-{i}", variant_name, aicte_id if use_exact_id else f"AICTE-DIFF-{i}")

        bureau_a = "bureau-rb"
        bureau_b = "bureau-pgrc"

        topics = [
            ("Fee Structure", "Excessive annual fee charged beyond AICTE norms", "Students forced to pay capitation and extra exam fees"),
            ("Infrastructure", "No computer lab equipment and broken air conditioning", "Laboratories lack basic computing facilities and internet connectivity"),
            ("Faculty Related", "Shortage of qualified professors and delayed faculty salaries", "Inadequate teaching staff, guest lecturers handling core subjects"),
        ]
        topic, sub_a, sub_b = topics[i % len(topics)]

        case_a = MockCase(f"case-a-{i}", inst_a, topic, sub_a, f"Detailed complaint regarding {sub_a} at campus.", bureau_a)
        case_b = MockCase(f"case-b-{i}", inst_b, topic, sub_b, f"Public grievance filed concerning {sub_b}.", bureau_b)

        pairs.append((case_a, case_b, True))

    # Generate Non-Overlaps (completely different colleges & issues)
    for i in range(n_samples // 2):
        inst_a = MockInst(f"diff-inst-a-{i}", f"North Valley College {i}", f"AICTE-NV-{i}", "Delhi")
        inst_b = MockInst(f"diff-inst-b-{i}", f"Southern Academy {i}", f"AICTE-SA-{i}", "Tamil Nadu")

        case_a = MockCase(f"neg-case-a-{i}", inst_a, "Admission", "Late entrance counselling", "Description A", "bureau-rb")
        case_b = MockCase(f"neg-case-b-{i}", inst_b, "Examination", "Hall ticket delay", "Description B", "bureau-pgrc")

        pairs.append((case_a, case_b, False))

    random.shuffle(pairs)
    return pairs


def evaluate_engine() -> Dict[str, Any]:
    dataset = generate_labelled_dataset(120)
    service = MatchingService()

    configs = {
        "rules_only": {"name": "Rules Only (AICTE ID + Exact Category)", "threshold": 0.50},
        "rules_fuzzy": {"name": "Rules + Fuzzy (Rapidfuzz + Normalization)", "threshold": 0.45},
        "rules_fuzzy_semantic": {"name": "Rules + Fuzzy + Semantic (Full Samanvay Engine)", "threshold": 0.45},
    }

    results = {}

    for key, cfg in configs.items():
        tp = 0
        fp = 0
        tn = 0
        fn = 0

        for c1, c2, is_overlap in dataset:
            if key == "rules_only":
                # Only matches if identical AICTE ID and exact category
                same_id = bool(c1.institution.aicte_permanent_id and c1.institution.aicte_permanent_id == c2.institution.aicte_permanent_id)
                same_cat = bool(c1.category == c2.category)
                predicted = same_id and same_cat
            elif key == "rules_fuzzy":
                # Exact + rapidfuzz institution match + category
                inst_score, _ = service.match_institutions(c1.institution, c2.institution)
                same_cat = bool(c1.category == c2.category)
                predicted = (inst_score >= 0.75 and same_cat)
            else:
                # Full 3-layer engine score
                score, _ = service.score_complaints(c1, c2)
                predicted = (score >= cfg["threshold"])

            if predicted and is_overlap:
                tp += 1
            elif predicted and not is_overlap:
                fp += 1
            elif not predicted and not is_overlap:
                tn += 1
            else:
                fn += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / len(dataset) if len(dataset) > 0 else 0.0

        results[key] = {
            "name": cfg["name"],
            "precision": round(precision * 100, 1),
            "recall": round(recall * 100, 1),
            "f1_score": round(f1 * 100, 1),
            "accuracy": round(accuracy * 100, 1),
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "total_tested": len(dataset),
        }

    return {
        "status": "success",
        "total_pairs_evaluated": len(dataset),
        "ground_truth_overlaps": sum(1 for _, _, y in dataset if y),
        "ground_truth_non_overlaps": sum(1 for _, _, y in dataset if not y),
        "metrics": results,
    }


def main():
    print("=" * 70)
    print("SAMANVAY OVERLAP ENGINE ACCURACY BENCHMARK HARNESS")
    print("=" * 70)
    data = evaluate_engine()
    print(f"Total labelled pairs tested: {data['total_pairs_evaluated']}")
    print(f"Ground-truth overlaps: {data['ground_truth_overlaps']} | Non-overlaps: {data['ground_truth_non_overlaps']}\n")

    print(f"{'Configuration':<46} | {'Precision':<9} | {'Recall':<7} | {'F1-Score':<8} | {'Accuracy':<8}")
    print("-" * 88)
    for k, v in data["metrics"].items():
        print(f"{v['name']:<46} | {v['precision']:>7.1f}% | {v['recall']:>5.1f}% | {v['f1_score']:>6.1f}% | {v['accuracy']:>6.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
