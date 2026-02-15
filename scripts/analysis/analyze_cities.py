"""City dataset analysis — index characteristics.

Reads cities.jsonl and reports on ambiguous city names, multi-word names,
case distribution, non-ASCII characters, name lengths, and word counts.
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
    """Load cities and print index characteristic statistics."""
    countries: Counter[str] = Counter()
    cities_per_country: dict[str, set[str]] = defaultdict(set)
    all_city_names: list[str] = []
    city_to_countries: dict[str, set[str]] = defaultdict(set)
    total = 0

    multi_word = 0
    case_upper = 0
    case_lower = 0
    case_mixed = 0
    has_non_ascii = 0

    city_name_lengths: list[int] = []
    multi_word_examples: list[tuple[str, str]] = []
    special_char_examples: list[tuple[str, str, list[str]]] = []

    with open(DATA_DIR / "cities.jsonl", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            city = obj["city"]
            country = obj["country"]
            total += 1
            countries[country] += 1
            cities_per_country[country].add(city)
            all_city_names.append(city)
            city_to_countries[city].add(country)

            if len(city.split()) > 1:
                multi_word += 1
                if len(multi_word_examples) < 20:
                    multi_word_examples.append((country, city))

            if city == city.upper():
                case_upper += 1
            elif city == city.lower():
                case_lower += 1
            else:
                case_mixed += 1

            if re.search(r"[^\x00-\x7F]", city):
                has_non_ascii += 1
                if len(special_char_examples) < 20:
                    chars = list(set(re.findall(r"[^\x00-\x7F]", city)))
                    special_char_examples.append((country, city, chars))

            city_name_lengths.append(len(city))

    _print_overview(total, countries, cities_per_country)
    _print_ambiguous(city_to_countries)
    _print_case_distribution(total, case_upper, case_lower, case_mixed)
    _print_multi_word(total, multi_word, multi_word_examples)
    _print_non_ascii(total, has_non_ascii, special_char_examples)
    _print_length_stats(all_city_names, city_name_lengths)
    _print_word_count_distribution(total, all_city_names)


def _print_overview(total: int, countries: Counter[str], cities_per_country: dict[str, set[str]]) -> None:
    """Print dataset overview and per-country city counts."""
    print("=" * 70)
    print("CITIES.JSONL ANALYSIS")
    print("=" * 70)
    print(f"Total entries: {total:,}")
    print(f"Unique countries: {len(countries)}")
    print(f"Unique city names (globally): {len(set(cities_per_country)):,}")
    print()
    print("CITIES PER COUNTRY:")
    for code, count in countries.most_common():
        unique = len(cities_per_country[code])
        print(f"  {code}: {count:,} entries, {unique:,} unique cities")
    print()


def _print_ambiguous(city_to_countries: dict[str, set[str]]) -> None:
    """Print cities that appear in multiple countries."""
    ambiguous = {city: sorted(ctries) for city, ctries in city_to_countries.items() if len(ctries) > 1}
    print(f"AMBIGUOUS CITIES (appearing in multiple countries): {len(ambiguous)}")
    sorted_ambiguous = sorted(ambiguous.items(), key=lambda x: -len(x[1]))
    for city, ctries in sorted_ambiguous[:30]:
        print(f"  '{city}' -> {ctries}")
    if len(sorted_ambiguous) > 30:
        print(f"  ... and {len(sorted_ambiguous) - 30} more ambiguous cities")
    print()


def _print_case_distribution(total: int, upper: int, lower: int, mixed: int) -> None:
    """Print case distribution of city names."""
    print("CASE DISTRIBUTION OF CITY NAMES:")
    print(f"  Title/Mixed Case: {mixed:,} ({mixed / total * 100:.1f}%)")
    print(f"  ALL UPPER: {upper:,} ({upper / total * 100:.1f}%)")
    print(f"  all lower: {lower:,} ({lower / total * 100:.1f}%)")
    print()


def _print_multi_word(total: int, multi_word: int, examples: list[tuple[str, str]]) -> None:
    """Print multi-word city name statistics."""
    print(f"MULTI-WORD CITY NAMES: {multi_word:,} / {total:,} ({multi_word / total * 100:.1f}%)")
    print("Examples:")
    for country, city in examples[:15]:
        print(f"  [{country}] {city}")
    print()


def _print_non_ascii(total: int, count: int, examples: list[tuple[str, str, list[str]]]) -> None:
    """Print non-ASCII character statistics in city names."""
    print(f"CITY NAMES WITH NON-ASCII CHARACTERS: {count:,} / {total:,} ({count / total * 100:.1f}%)")
    print("Examples:")
    for country, city, chars in examples[:15]:
        print(f"  [{country}] {city}  (chars: {chars})")
    print()


def _print_length_stats(all_city_names: list[str], lengths: list[int]) -> None:
    """Print city name length statistics."""
    avg_len = sum(lengths) / len(lengths)
    max_len = max(lengths)
    min_len = min(lengths)
    longest = [n for n in all_city_names if len(n) == max_len][:3]
    shortest = [n for n in all_city_names if len(n) == min_len][:5]
    print("CITY NAME LENGTH STATS:")
    print(f"  Average: {avg_len:.1f} characters")
    print(f"  Min: {min_len} characters -> examples: {shortest}")
    print(f"  Max: {max_len} characters -> examples: {longest}")
    print()


def _print_word_count_distribution(total: int, all_city_names: list[str]) -> None:
    """Print distribution of word counts in city names."""
    word_counts: Counter[int] = Counter(len(city.split()) for city in all_city_names)
    print("WORD COUNT DISTRIBUTION IN CITY NAMES:")
    for wc, count in sorted(word_counts.items()):
        print(f"  {wc} word(s): {count:,} ({count / total * 100:.1f}%)")


if __name__ == "__main__":
    main()
