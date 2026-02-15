"""Cross-analysis of addresses and cities datasets.

Compares country coverage between both files, identifies addresses
where city extraction is difficult, analyzes structural patterns
per country, and examines country-specific postal code formats.
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
    """Run cross-analysis between addresses and cities datasets."""
    addr_countries: set[str] = set()
    city_countries: set[str] = set()

    addr_data: list[dict[str, str]] = []
    with open(DATA_DIR / "addresses.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            addr_countries.add(obj["country"])
            addr_data.append(obj)

    cities_by_country: dict[str, set[str]] = defaultdict(set)
    with open(DATA_DIR / "cities.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            city_countries.add(obj["country"])
            cities_by_country[obj["country"]].add(obj["city"].lower())

    _print_country_overlap(addr_countries, city_countries)
    _print_difficult_addresses(addr_data)
    _print_structure_patterns(addr_data, addr_countries)
    _print_estonian_addresses(addr_data)
    _print_dutch_postal_codes(addr_data)
    _print_polish_postal_codes(addr_data)
    _print_swedish_postal_codes(addr_data)
    _print_italian_patterns(addr_data)


def _print_country_overlap(addr_countries: set[str], city_countries: set[str]) -> None:
    """Print country coverage comparison between both datasets."""
    print("=" * 70)
    print("CROSS-ANALYSIS")
    print("=" * 70)
    print()
    print("COUNTRY OVERLAP:")
    print(f"  Countries in addresses.jsonl: {sorted(addr_countries)}")
    print(f"  Countries in cities.jsonl:    {sorted(city_countries)}")
    in_both = addr_countries & city_countries
    only_addr = addr_countries - city_countries
    only_city = city_countries - addr_countries
    print(f"  In both:                      {sorted(in_both)}")
    print(f"  Only in addresses:            {sorted(only_addr) if only_addr else 'None'}")
    print(f"  Only in cities:               {sorted(only_city) if only_city else 'None'}")
    print()


def _print_difficult_addresses(addr_data: list[dict[str, str]]) -> None:
    """Print addresses where city extraction is particularly challenging."""
    print("=" * 70)
    print("ADDRESSES WHERE CITY EXTRACTION IS DIFFICULT")
    print("=" * 70)
    print()

    starts_with_comma: list[tuple[str, str]] = []
    single_word: list[tuple[str, str]] = []
    very_short: list[tuple[str, str]] = []
    very_long: list[tuple[str, str]] = []
    only_numbers: list[tuple[str, str]] = []
    has_parens: list[tuple[str, str]] = []
    multi_dashes: list[tuple[str, str]] = []
    has_slash: list[tuple[str, str]] = []

    for obj in addr_data:
        addr = obj["address"]
        country = obj["country"]

        if not addr.strip():
            continue

        if addr.startswith(",") and len(starts_with_comma) < 10:
            starts_with_comma.append((country, addr))
        if "," not in addr and not re.search(r"\d", addr) and " " not in addr.strip() and len(single_word) < 10:
            single_word.append((country, addr))
        if len(addr) <= 3:
            very_short.append((country, addr))
        if len(addr) > 100 and len(very_long) < 10:
            very_long.append((country, addr))
        if re.match(r"^[\d\s]+$", addr) and len(only_numbers) < 10:
            only_numbers.append((country, addr))
        if ("(" in addr or ")" in addr) and len(has_parens) < 10:
            has_parens.append((country, addr))
        if addr.count("-") >= 3 and len(multi_dashes) < 10:
            multi_dashes.append((country, addr))
        if "/" in addr and len(has_slash) < 10:
            has_slash.append((country, addr))

    _print_edge_case("1. ADDRESSES STARTING WITH COMMA", starts_with_comma)
    _print_edge_case("2. SINGLE-WORD ADDRESSES (no comma, no number, no space)", single_word)

    print(f"3. VERY SHORT ADDRESSES (<=3 chars): {len(very_short)} total")
    for country, addr in very_short[:10]:
        print(f"   [{country}] '{addr}'")
    print()

    _print_edge_case("4. VERY LONG ADDRESSES (>100 chars)", very_long[:5])
    _print_edge_case("5. ADDRESSES WITH ONLY NUMBERS", only_numbers)
    _print_edge_case("6. ADDRESSES WITH PARENTHESES", has_parens)
    _print_edge_case("7. ADDRESSES WITH MULTIPLE DASHES (>=3)", multi_dashes)
    _print_edge_case("8. ADDRESSES WITH SLASHES", has_slash)


def _print_edge_case(label: str, items: list[tuple[str, str]]) -> None:
    """Print a labeled list of edge-case addresses."""
    print(f"{label}:")
    for country, addr in items:
        print(f"   [{country}] {addr}")
    print()


def _print_structure_patterns(addr_data: list[dict[str, str]], addr_countries: set[str]) -> None:
    """Print address structure pattern distribution per country."""
    print("=" * 70)
    print("ADDRESS STRUCTURE PATTERNS BY COUNTRY")
    print("=" * 70)
    print()

    for country in sorted(addr_countries):
        addrs = [o["address"] for o in addr_data if o["country"] == country]
        sample_size = min(len(addrs), 1000)
        sample = addrs[:sample_size]

        patterns: Counter[str] = Counter()
        for addr in sample:
            parts: list[str] = []
            if re.search(r"\d{4,6}", addr):
                parts.append("postal")
            if "," in addr:
                parts.append("comma")
            if re.search(r"\d+", addr) and not re.search(r"\d{4,6}", addr):
                parts.append("number")
            if not parts:
                parts.append("plain")
            patterns["+".join(sorted(parts))] += 1

        print(f"  {country} (sample of {sample_size}):")
        for pattern, count in patterns.most_common(5):
            print(f"    {pattern}: {count} ({count / sample_size * 100:.1f}%)")
        print()


def _print_estonian_addresses(addr_data: list[dict[str, str]]) -> None:
    """Print Estonian address samples showing unique vald/küla structure."""
    print("=" * 70)
    print("ESTONIAN (EE) ADDRESS SPECIAL ANALYSIS (high comma rate 80%)")
    print("=" * 70)
    ee_addrs = [o["address"] for o in addr_data if o["country"] == "EE"]
    for addr in ee_addrs[:15]:
        print(f"  {addr}")
    print()


def _print_dutch_postal_codes(addr_data: list[dict[str, str]]) -> None:
    """Print Dutch alphanumeric postal code (NNNNLL) pattern analysis."""
    print("=" * 70)
    print("DUTCH (NL) POSTAL CODE PATTERNS (alphanumeric)")
    print("=" * 70)
    nl_addrs = [o["address"] for o in addr_data if o["country"] == "NL"]
    nl_postal = [a for a in nl_addrs if re.search(r"\d{4}[A-Za-z]{2}", a)]
    print(f"  Dutch addresses with pattern NNNNLL: {len(nl_postal):,}/{len(nl_addrs):,}")
    for addr in nl_postal[:10]:
        print(f"  {addr}")
    print()


def _print_polish_postal_codes(addr_data: list[dict[str, str]]) -> None:
    """Print Polish postal code (NN-NNN) pattern analysis."""
    print("=" * 70)
    print("POLISH (PL) POSTAL CODE PATTERNS (NN-NNN format)")
    print("=" * 70)
    pl_addrs = [o["address"] for o in addr_data if o["country"] == "PL"]
    pl_postal = [a for a in pl_addrs if re.search(r"\d{2}-\d{3}", a)]
    print(f"  Polish addresses with NN-NNN pattern: {len(pl_postal):,}/{len(pl_addrs):,}")
    for addr in pl_postal[:10]:
        print(f"  {addr}")
    print()


def _print_swedish_postal_codes(addr_data: list[dict[str, str]]) -> None:
    """Print Swedish postal code (NNN NN) pattern analysis."""
    print("=" * 70)
    print("SWEDISH (SE) POSTAL CODE PATTERNS")
    print("=" * 70)
    se_addrs = [o["address"] for o in addr_data if o["country"] == "SE"]
    se_postal = [a for a in se_addrs if re.search(r"\d{3}\s?\d{2}", a)]
    print(f"  Swedish addresses with NNN NN pattern: {len(se_postal):,}/{len(se_addrs):,}")
    for addr in se_postal[:10]:
        print(f"  {addr}")
    print()


def _print_italian_patterns(addr_data: list[dict[str, str]]) -> None:
    """Print Italian address pattern analysis (province codes)."""
    print("=" * 70)
    print("ITALIAN (IT) ADDRESS PATTERNS")
    print("=" * 70)
    it_addrs = [o["address"] for o in addr_data if o["country"] == "IT"]
    it_prov = [a for a in it_addrs if re.search(r"\([A-Z]{2}\)", a)]
    print(f"  Italian addresses with province code (XX): {len(it_prov):,}/{len(it_addrs):,}")
    for addr in it_prov[:10]:
        print(f"  {addr}")


if __name__ == "__main__":
    main()
