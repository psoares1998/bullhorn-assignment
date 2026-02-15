"""Supplementary dataset analysis — ratios, encoding issues, and edge cases.

Computes address-to-city ratios per country, detects mojibake encoding
artifacts, identifies city-only addresses, separator patterns, and
duplicate entries.
"""

import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "address_classification_dataset" / "dataset"


def main() -> None:
    """Run supplementary analysis on both datasets."""
    cities_by_country: dict[str, set[str]] = defaultdict(set)
    with open(DATA_DIR / "cities.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            cities_by_country[obj["country"]].add(obj["city"])

    addr_count_by_country: Counter[str] = Counter()
    with open(DATA_DIR / "addresses.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            addr_count_by_country[obj["country"]] += 1

    total_addrs = sum(addr_count_by_country.values())

    _print_ratios(addr_count_by_country, cities_by_country)
    _print_mojibake()
    _print_empty_addresses()
    _print_city_only_addresses(addr_count_by_country, cities_by_country)
    _print_separator_patterns(total_addrs)
    _print_duplicates()


def _print_ratios(addr_counts: Counter[str], cities: dict[str, set[str]]) -> None:
    """Print address-to-city ratio per country."""
    print("=" * 70)
    print("ADDRESSES TO CITIES RATIO BY COUNTRY")
    print("=" * 70)
    print(f"{'Country':<10} {'Addresses':>12} {'Cities':>10} {'Ratio (addr/city)':>20}")
    print("-" * 55)
    for country in sorted(addr_counts.keys()):
        a = addr_counts[country]
        c = len(cities[country])
        ratio = a / c if c > 0 else float("inf")
        print(f"{country:<10} {a:>12,} {c:>10,} {ratio:>18.1f}")
    print()


def _print_mojibake() -> None:
    """Detect and print addresses with common mojibake encoding artifacts."""
    print("=" * 70)
    print("ADDRESSES WITH POTENTIAL ENCODING ISSUES (MOJIBAKE)")
    print("=" * 70)
    mojibake_pattern = re.compile(
        r"ã©|ã¨|ã |ã¹|ã§|ã®|ã´|ã¢|ã£|ã¯|â€™|Ã©|Ã¨|Ã |Ã¹|Ã§|Ã®|Ã´|Ã¢|Ã£|Ã¯",  # noqa: RUF001
        re.IGNORECASE,
    )
    mojibake_count = 0
    mojibake_examples: list[tuple[str, str]] = []
    with open(DATA_DIR / "addresses.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            addr = obj["address"]
            if mojibake_pattern.search(addr):
                mojibake_count += 1
                if len(mojibake_examples) < 15:
                    mojibake_examples.append((obj["country"], addr))

    print(f"Total addresses with mojibake patterns: {mojibake_count:,}")
    for country, addr in mojibake_examples:
        print(f"  [{country}] {addr}")
    print()


def _print_empty_addresses() -> None:
    """Print count of empty or whitespace-only addresses."""
    print("=" * 70)
    print("EDGE CASE: EMPTY/WHITESPACE-ONLY ADDRESSES")
    print("=" * 70)
    empty_count = 0
    whitespace_only = 0
    with open(DATA_DIR / "addresses.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            addr = obj["address"]
            if not addr:
                empty_count += 1
            elif not addr.strip():
                whitespace_only += 1
    print(f"  Empty strings: {empty_count}")
    print(f"  Whitespace only: {whitespace_only}")
    print()


def _print_city_only_addresses(addr_counts: Counter[str], cities: dict[str, set[str]]) -> None:
    """Print addresses that consist of only a city name with no additional info."""
    print("=" * 70)
    print("ADDITIONAL FORMAT PATTERNS")
    print("=" * 70)
    print()

    city_only_count: Counter[str] = Counter()
    city_only_examples: dict[str, list[str]] = defaultdict(list)

    cities_upper: dict[str, set[str]] = {country: {c.upper() for c in city_set} for country, city_set in cities.items()}

    with open(DATA_DIR / "addresses.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            addr = obj["address"].strip()
            country = obj["country"]
            if addr.upper() in cities_upper.get(country, set()):
                city_only_count[country] += 1
                if len(city_only_examples[country]) < 3:
                    city_only_examples[country].append(addr)

    print("ADDRESSES THAT ARE JUST A CITY NAME (no street/postal):")
    for country in sorted(city_only_count.keys()):
        c = city_only_count[country]
        t = addr_counts[country]
        print(f"  {country}: {c:,}/{t:,} ({c / t * 100:.1f}%) - e.g. {city_only_examples[country]}")
    total_city_only = sum(city_only_count.values())
    total_addrs = sum(addr_counts.values())
    print(f"  TOTAL: {total_city_only:,}/{total_addrs:,} ({total_city_only / total_addrs * 100:.1f}%)")
    print()


def _print_separator_patterns(total_addrs: int) -> None:
    """Print address separator pattern distribution."""
    print("ADDRESSES WITH SEPARATOR PATTERNS:")
    separator_stats: Counter[str] = Counter()
    with open(DATA_DIR / "addresses.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            addr = obj["address"]
            if " - " in addr:
                separator_stats["space-dash-space"] += 1
            elif ", " in addr:
                separator_stats["comma-space"] += 1
            elif "," in addr:
                separator_stats["comma-nospace"] += 1
            else:
                separator_stats["space-only"] += 1

    for sep, count in separator_stats.most_common():
        pct = count / total_addrs * 100
        print(f"  {sep}: {count:,} ({pct:.1f}%)")
    print()


def _print_duplicates() -> None:
    """Print duplicate address statistics."""
    print("DUPLICATE ADDRESSES:")
    addr_counter: Counter[tuple[str, str]] = Counter()
    with open(DATA_DIR / "addresses.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            key = (obj["address"], obj["country"])
            addr_counter[key] += 1

    dupes = {k: v for k, v in addr_counter.items() if v > 1}
    print(f"  Total unique (address, country) pairs: {len(addr_counter):,}")
    print(f"  Pairs appearing more than once: {len(dupes):,}")
    if dupes:
        top_dupes = sorted(dupes.items(), key=lambda x: -x[1])[:10]
        print("  Top duplicated addresses:")
        for (addr, country), count in top_dupes:
            print(f"    [{country}] '{addr}' x{count}")


if __name__ == "__main__":
    main()
