"""FlashText keyword index and reference data construction.

Builds the in-memory data structures used by the classification pipeline:
- Two FlashText KeywordProcessors (NFC and folded) for city name extraction
- Two city-to-countries mappings for precise and fallback matching
"""

import unicodedata
from collections import defaultdict

from flashtext import KeywordProcessor

from src.services.normalizer import accent_fold, normalize


def _build_non_word_boundaries() -> set[str]:
    """Build a set of characters that FlashText should treat as part of words.

    By default, FlashText only considers ASCII letters and digits as
    word characters. This function extends the set to include:

    - **Unicode letters (L)** — accented characters like ü, ö, ç are
      part of words, not separators.
    - **Numbers (N)** — digits are part of words.
    - **Hyphens** — so that hyphenated compounds like "albert-troppmair-weg"
      are treated as a single token, preventing false matches on parts
      of street names (e.g., "albert" matching as a French city).
      Hyphenated city names like "oud-turnhout" still match because
      they are stored in the index with the hyphen.

    Combining marks (M) are not needed because ``normalize`` uses NFC,
    which composes accented characters into single codepoints.
    """
    non_word = set()
    for codepoint in range(0x10000):
        char = chr(codepoint)
        category = unicodedata.category(char)
        if category[0] in ("L", "N"):
            non_word.add(char)
    non_word.add("-")
    return non_word


def build_city_index(
    city_pairs: list[tuple[str, str]],
) -> tuple[KeywordProcessor, dict[str, set[str]], KeywordProcessor, dict[str, set[str]]]:
    """Build two separate FlashText indexes: NFC and accent-folded.

    The NFC index preserves accent distinctions — "Lipa" (SI) and
    "Lípa" (CZ) remain separate entries. The folded index catches
    input where accents were dropped — "grossglockner" matches
    "Großglockner" (AT).

    At query time, the NFC index is tried first (more precise).
    The folded index is used as fallback only when NFC finds nothing.

    Args:
        city_pairs: List of (city_name, country_code) tuples from the loader.

    Returns:
        A tuple of:
        - ``nfc_processor``: FlashText index with NFC city names.
        - ``nfc_city_to_countries``: NFC city name to country codes.
        - ``folded_processor``: FlashText index with folded city names.
        - ``folded_city_to_countries``: Folded city name to country codes.
    """
    non_word = _build_non_word_boundaries()

    nfc_processor = KeywordProcessor()
    nfc_processor.set_non_word_boundaries(non_word)
    nfc_city_to_countries: dict[str, set[str]] = defaultdict(set)

    folded_processor = KeywordProcessor()
    folded_processor.set_non_word_boundaries(non_word)
    folded_city_to_countries: dict[str, set[str]] = defaultdict(set)

    for city_name, country_code in city_pairs:
        normalized = normalize(city_name)
        folded = accent_fold(normalized)

        # NFC index — exact accented forms.
        nfc_city_to_countries[normalized].add(country_code)
        nfc_processor.add_keyword(normalized, normalized)

        # Folded index — all cities in accent-free form.
        folded_city_to_countries[folded].add(country_code)
        folded_processor.add_keyword(folded, folded)

    return (
        nfc_processor,
        dict(nfc_city_to_countries),
        folded_processor,
        dict(folded_city_to_countries),
    )
