"""Generate misclassifications.txt with all incorrectly classified addresses."""

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.index import build_city_index  # noqa: E402
from src.data.loader import load_cities  # noqa: E402
from src.services.normalizer import normalize  # noqa: E402
from src.services.pipeline import ClassificationPipeline  # noqa: E402

DATA_DIR = PROJECT_ROOT / "address_classification_dataset" / "dataset"
OUTPUT = Path(__file__).resolve().parent.parent / "output" / "misclassifications.txt"


def main() -> None:
    """Run pipeline on all addresses and write misclassifications to file."""
    print("Loading city index...")
    city_pairs = load_cities()
    nfc_proc, nfc_ctc, fold_proc, fold_ctc = build_city_index(city_pairs)
    pipeline = ClassificationPipeline(nfc_proc, nfc_ctc, fold_proc, fold_ctc)

    misclassified: list[str] = []
    total = 0
    correct = 0

    t0 = time.perf_counter()
    with open(DATA_DIR / "addresses_filtered.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            address = obj["address"]
            expected = obj["country"]
            predicted = pipeline.classify(address)
            total += 1

            if predicted == expected:
                correct += 1
            else:
                components = pipeline._parse_address(normalize(address))
                parsing = " | ".join(f"{k}={v}" for k, v in components.items())
                misclassified.append(f"[{expected} -> {predicted}] {address}\n  parsing: {parsing}")

    t1 = time.perf_counter()

    with open(OUTPUT, "w", encoding="utf-8") as f:
        for entry in misclassified:
            f.write(entry + "\n")

    print(f"Done in {t1 - t0:.2f}s — {correct}/{total} correct ({correct / total * 100:.2f}%)")
    print(f"Wrote {len(misclassified)} misclassifications to {OUTPUT.name}")


if __name__ == "__main__":
    main()
