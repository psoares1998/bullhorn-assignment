"""Address formatting patterns analysis.

Analyzes structural characteristics of addresses: case distribution,
comma usage, postal codes, country name presence, dashes, and
non-ASCII characters. Outputs per-country breakdowns for each pattern.
"""

import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "address_classification_dataset" / "dataset"

COUNTRY_NAMES: dict[str, list[str]] = {
    "AT": ["austria", "österreich"],
    "BE": ["belgium", "belgique", "belgië", "belgien"],
    "CZ": ["czech", "česko", "czechia"],
    "DE": ["germany", "deutschland"],
    "EE": ["estonia", "eesti"],
    "FR": ["france"],
    "IT": ["italy", "italia"],
    "LU": ["luxembourg", "luxemburg"],
    "NL": ["netherlands", "nederland", "holland"],
    "PL": ["poland", "polska"],
    "PT": ["portugal"],
    "RO": ["romania", "românia"],
    "SE": ["sweden", "sverige"],
    "SI": ["slovenia", "slovenija"],
    "SK": ["slovakia", "slovensko"],
}


def main() -> None:
    """Load addresses and print formatting pattern statistics."""
    countries: Counter[str] = Counter()
    total = 0
    sample_addresses: dict[str, list[str]] = defaultdict(list)

    has_country_name: Counter[str] = Counter()
    has_postal_code: Counter[str] = Counter()
    has_comma: Counter[str] = Counter()
    has_number: Counter[str] = Counter()
    has_dash: Counter[str] = Counter()
    case_stats: Counter[str] = Counter()

    with open(DATA_DIR / "addresses.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            country = obj["country"]
            address = obj["address"]
            total += 1
            countries[country] += 1
            if len(sample_addresses[country]) < 5:
                sample_addresses[country].append(address)

            if "," in address:
                has_comma[country] += 1
            if re.search(r"\d", address):
                has_number[country] += 1
            if "-" in address:
                has_dash[country] += 1

            if address == address.upper():
                case_stats["ALL_UPPER"] += 1
            elif address == address.lower():
                case_stats["all_lower"] += 1
            else:
                case_stats["Mixed_Case"] += 1

            addr_lower = address.lower()
            if country in COUNTRY_NAMES:
                for name in COUNTRY_NAMES[country]:
                    if name in addr_lower:
                        has_country_name[country] += 1
                        break

            if re.search(r"\b\d{4,6}\b", address):
                has_postal_code[country] += 1

    non_ascii_count = 0
    with open(DATA_DIR / "addresses.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            if re.search(r"[^\x00-\x7F]", obj["address"]):
                non_ascii_count += 1

    sorted_countries = countries.most_common()

    print()
    print("=" * 70)
    print("ADDRESS FORMATTING PATTERNS")
    print("=" * 70)
    print()

    print("CASE DISTRIBUTION:")
    for case, count in case_stats.most_common():
        print(f"  {case}: {count:,} ({count / total * 100:.1f}%)")
    print()

    _print_country_metric("ADDRESSES CONTAINING COMMAS", has_comma, countries, sorted_countries)
    _print_country_metric("ADDRESSES CONTAINING NUMBERS", has_number, countries, sorted_countries)
    _print_country_metric(
        "ADDRESSES CONTAINING POSTAL CODES (4-6 digit sequences)", has_postal_code, countries, sorted_countries
    )
    _print_country_metric("ADDRESSES CONTAINING COUNTRY NAME", has_country_name, countries, sorted_countries)
    _print_country_metric("ADDRESSES WITH DASHES/HYPHENS", has_dash, countries, sorted_countries)

    print("TOTAL ADDRESSES WITH NON-ASCII CHARACTERS:")
    print(f"  {non_ascii_count:,} / {total:,} ({non_ascii_count / total * 100:.1f}%)")


def _print_country_metric(
    label: str,
    metric: Counter[str],
    totals: Counter[str],
    sorted_countries: list[tuple[str, int]],
) -> None:
    """Print a per-country breakdown of a given metric."""
    print(f"{label} (by country):")
    for country, _ in sorted_countries:
        ct = metric.get(country, 0)
        tot = totals[country]
        print(f"  {country}: {ct:,}/{tot:,} ({ct / tot * 100:.1f}%)")
    print()


if __name__ == "__main__":
    main()
