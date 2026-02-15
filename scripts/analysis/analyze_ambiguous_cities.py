"""Analyze ambiguous cities — same exact name (case-insensitive) in multiple countries."""

import json
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CITIES_PATH = PROJECT_ROOT / "address_classification_dataset" / "dataset" / "cities.jsonl"


def main() -> None:
    """Find cities that appear in multiple countries with the exact same name."""
    # Group countries by lowercase city name (preserving accents).
    city_countries: dict[str, set[str]] = defaultdict(set)

    with open(CITIES_PATH, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            city = obj["city"].strip().lower()
            country = obj["country"]
            city_countries[city].add(country)

    # Filter to ambiguous cities (2+ countries).
    ambiguous = {city: countries for city, countries in city_countries.items() if len(countries) > 1}

    # Sort by number of countries (descending), then alphabetically.
    sorted_ambiguous = sorted(ambiguous.items(), key=lambda x: (-len(x[1]), x[0]))

    print(f"Total unique city names (lowercase): {len(city_countries)}")
    print(f"Ambiguous cities (2+ countries): {len(ambiguous)}")
    print()

    # Group by number of countries.
    by_count: dict[int, int] = defaultdict(int)
    for _, countries in sorted_ambiguous:
        by_count[len(countries)] += 1

    for n, count in sorted(by_count.items(), reverse=True):
        print(f"  {n} countries: {count} cities")
    print()

    # Write all ambiguous cities to file and print.
    output = Path(__file__).resolve().parent.parent / "output" / "ambiguous_cities.txt"
    with open(output, "w", encoding="utf-8") as out:
        for city, countries in sorted_ambiguous:
            codes = ", ".join(sorted(countries))
            line = f"{city} -> {codes}"
            out.write(line + "\n")
    print(f"Full list written to {output.name}")


if __name__ == "__main__":
    main()
