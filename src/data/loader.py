"""Dataset loading utilities.

Reads cities.jsonl and provides structured data for index construction.
"""

import json
from pathlib import Path

# Default dataset location relative to the project root.
_DEFAULT_DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "address_classification_dataset" / "dataset"


def load_cities(dataset_dir: Path | None = None) -> list[tuple[str, str]]:
    """Load city-country pairs from cities.jsonl.

    Args:
        dataset_dir: Directory containing the dataset files.
            Defaults to ``address_classification_dataset/dataset/``.

    Returns:
        List of (city_name, country_code) tuples.

    Raises:
        FileNotFoundError: If cities.jsonl does not exist.
    """
    dataset_dir = dataset_dir or _DEFAULT_DATASET_DIR
    cities_path = dataset_dir / "cities.jsonl"

    pairs: list[tuple[str, str]] = []
    with open(cities_path, encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line.strip())
            pairs.append((obj["city"], obj["country"]))
    return pairs
