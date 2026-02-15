"""Filter out addresses that contain only an ambiguous city name with no other info.

Produces:
- addresses_filtered.jsonl — cleaned dataset
- addresses_removed.txt — list of removed addresses
"""

import json
import re
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "address_classification_dataset" / "dataset"
CITIES_PATH = DATA_DIR / "cities.jsonl"
ADDRESSES_PATH = DATA_DIR / "addresses.jsonl"
OUTPUT_JSONL = DATA_DIR / "addresses_filtered.jsonl"
OUTPUT_REMOVED = Path(__file__).resolve().parent.parent / "output" / "addresses_removed.txt"


def load_ambiguous_cities() -> set[str]:
    """Load city names that appear in 2+ countries (lowercase, preserving accents)."""
    city_countries: dict[str, set[str]] = defaultdict(set)
    with open(CITIES_PATH, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            city = obj["city"].strip().lower()
            country = obj["country"]
            city_countries[city].add(country)
    return {city for city, countries in city_countries.items() if len(countries) > 1}


def is_only_ambiguous_city(address: str, ambiguous: set[str]) -> bool:
    """Check if an address contains only an ambiguous city name (possibly repeated)."""
    # Remove punctuation and separators, keep only words.
    cleaned = re.sub(r"[,\-.\s/\\:;()]+", " ", address.lower()).strip()
    words = cleaned.split()

    if not words:
        return False

    # All words must be the same ambiguous city.
    unique_words = set(words)
    return len(unique_words) == 1 and unique_words.pop() in ambiguous


def main() -> None:
    """Filter addresses and write outputs."""
    ambiguous = load_ambiguous_cities()
    print(f"Loaded {len(ambiguous)} ambiguous city names")

    kept = 0
    removed_entries: list[str] = []

    with (
        open(ADDRESSES_PATH, encoding="utf-8") as f_in,
        open(OUTPUT_JSONL, "w", encoding="utf-8") as f_out,
    ):
        for line in f_in:
            obj = json.loads(line.strip())
            address = obj["address"]
            country = obj["country"]

            if is_only_ambiguous_city(address, ambiguous):
                removed_entries.append(f"[{country}] {address}")
            else:
                f_out.write(line)
                kept += 1

    with open(OUTPUT_REMOVED, "w", encoding="utf-8") as f:
        for entry in removed_entries:
            f.write(entry + "\n")

    total = kept + len(removed_entries)
    print(f"Total: {total}")
    print(f"Kept: {kept}")
    print(f"Removed: {len(removed_entries)}")
    print(f"Written to: {OUTPUT_JSONL.name}")
    print(f"Removed list: {OUTPUT_REMOVED.name}")


if __name__ == "__main__":
    main()
