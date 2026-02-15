"""Address dataset analysis — volume and distribution.

Reads addresses.jsonl and outputs per-country counts, percentages,
and sample addresses. This is the first step of the EDA pipeline.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "address_classification_dataset" / "dataset"


def main() -> None:
    """Load addresses and print country distribution statistics."""
    countries: Counter[str] = Counter()
    total = 0
    sample_addresses: dict[str, list[str]] = defaultdict(list)

    with open(DATA_DIR / "addresses.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            country = obj["country"]
            address = obj["address"]
            total += 1
            countries[country] += 1
            if len(sample_addresses[country]) < 5:
                sample_addresses[country].append(address)

    print("=" * 70)
    print("ADDRESSES.JSONL ANALYSIS")
    print("=" * 70)
    print(f"Total addresses: {total:,}")
    print(f"Unique countries (by ISO code): {len(countries)}")
    print()

    sorted_countries = countries.most_common()
    print("ALL COUNTRY CODES (sorted by count):")
    for code, count in sorted_countries:
        pct = count / total * 100
        print(f"  {code}: {count:>8,} ({pct:>6.2f}%)")
    print()


if __name__ == "__main__":
    main()
