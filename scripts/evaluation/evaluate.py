"""Evaluate the classification pipeline against addresses.jsonl.

Loads the full labeled dataset and runs every address through the
pipeline, reporting overall accuracy and per-country metrics.
"""

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

# Add project root to path so src is importable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.index import build_city_index  # noqa: E402
from src.data.loader import load_cities  # noqa: E402
from src.services.pipeline import ClassificationPipeline  # noqa: E402

DATA_DIR = PROJECT_ROOT / "address_classification_dataset" / "dataset"


def main() -> None:
    """Run evaluation and print results."""
    print("Loading city index...")
    t0 = time.perf_counter()
    city_pairs = load_cities()
    nfc_proc, nfc_ctc, fold_proc, fold_ctc = build_city_index(city_pairs)
    pipeline = ClassificationPipeline(nfc_proc, nfc_ctc, fold_proc, fold_ctc)
    t1 = time.perf_counter()
    print(f"Index built in {t1 - t0:.2f}s ({len(nfc_ctc):,} NFC + {len(fold_ctc):,} folded entries)")

    print("Evaluating against addresses.jsonl...")
    total = 0
    correct = 0
    unresolved = 0
    misclassified_examples: list[tuple[str, str, str | None]] = []

    # confusion[expected][predicted] = count
    confusion: dict[str, Counter[str]] = defaultdict(Counter)

    t2 = time.perf_counter()
    with open(DATA_DIR / "addresses_filtered.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            address = obj["address"]
            expected = obj["country"]

            predicted = pipeline.classify(address)
            total += 1
            confusion[expected][predicted or "NULL"] += 1

            if predicted == expected:
                correct += 1
            elif predicted is None:
                unresolved += 1
                if len(misclassified_examples) < 20:
                    misclassified_examples.append((address, expected, predicted))
            else:
                if len(misclassified_examples) < 20:
                    misclassified_examples.append((address, expected, predicted))

    t3 = time.perf_counter()
    accuracy = correct / total * 100 if total else 0
    all_countries = sorted(confusion.keys())

    # --- Overall ---
    print()
    print("=" * 70)
    print(f"OVERALL: {correct:,}/{total:,} correct ({accuracy:.2f}%)")
    print(f"Unresolved (null): {unresolved:,} ({unresolved / total * 100:.2f}%)")
    print(f"Evaluation time: {t3 - t2:.2f}s ({total / (t3 - t2):,.0f} addr/s)")
    print("=" * 70)

    # --- Per-country metrics (Precision / Recall / F1) ---
    print()
    print(f"{'Country':<8} {'Total':>8} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-" * 50)

    total_tp = 0
    total_fp = 0
    total_fn = 0
    country_stats: list[tuple[str, int, int, int, int]] = []

    for country in all_countries:
        tp = confusion[country][country]
        country_total = sum(confusion[country].values())
        fn = country_total - tp
        fp = sum(confusion[other][country] for other in all_countries if other != country)

        precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        total_tp += tp
        total_fp += fp
        total_fn += fn
        country_stats.append((country, country_total, tp, fp, fn))

        print(f"{country:<8} {country_total:>8,} {precision:>9.2f}% {recall:>9.2f}% {f1:>9.2f}%")

    # Macro averages: simple mean of per-country metrics.
    n = len(all_countries)
    precisions = []
    recalls = []
    f1s = []
    for _country, _country_total, tp, fp, fn in country_stats:
        p = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
        r = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
        f = 2 * p * r / (p + r) if (p + r) > 0 else 0
        precisions.append(p)
        recalls.append(r)
        f1s.append(f)
    macro_p = sum(precisions) / n
    macro_r = sum(recalls) / n
    macro_f1 = sum(f1s) / n
    print("-" * 50)
    print(f"{'AVERAGE':<8} {total:>8,} {macro_p:>9.2f}% {macro_r:>9.2f}% {macro_f1:>9.2f}%")

    # --- Sample misclassifications ---
    if misclassified_examples:
        print()
        print("Sample misclassifications:")
        for address, expected, predicted in misclassified_examples:
            print(f"  [{expected} -> {predicted}] {address[:80]}")


if __name__ == "__main__":
    main()
