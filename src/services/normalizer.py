"""L0 — Text normalization for address classification.

Handles case folding, Unicode normalization, accent folding, and
whitespace cleanup. Applied both at index build time (city names)
and per-request (incoming addresses).
"""

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")
_LEADING_COMMA_RE = re.compile(r"^,\s*")
_PARENTHESES_RE = re.compile(r"[()[\]]")

# Characters that NFKD decomposition does not handle correctly.
# These need explicit mapping before the combining-mark strip.
_SPECIAL_FOLDS: dict[str, str] = {
    "ß": "ss",
    "ł": "l",
    "Ł": "l",
    "ø": "o",
    "Ø": "o",
    "æ": "ae",
    "Æ": "ae",
    "œ": "oe",
    "Œ": "oe",
    "đ": "d",
    "Đ": "d",
}
_SPECIAL_FOLDS_TABLE = str.maketrans(_SPECIAL_FOLDS)


def normalize(text: str) -> str:
    """Normalize an address or city name for consistent matching.

    Operations (in order):
    1. Case folding to lowercase
    2. Unicode NFC normalization (composes accented characters into
       single codepoints, e.g. u + combining diaeresis → ü)
    3. Remove parentheses and brackets
    4. Whitespace normalization (collapse multiple spaces, trim)
    5. Leading comma removal

    Args:
        text: Raw address or city name string.

    Returns:
        Normalized string with accents preserved as single characters,
        case and whitespace standardized.
    """
    text = text.lower()
    text = unicodedata.normalize("NFC", text)
    text = _PARENTHESES_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    text = _LEADING_COMMA_RE.sub("", text)
    return text


def accent_fold(text: str) -> str:
    """Remove accents and diacritics from a normalized string.

    Produces an ASCII-friendly variant for fuzzy comparison.
    For example: ``kitzbühel`` -> ``kitzbuhel``.

    Handles special characters that NFKD decomposition alone
    cannot resolve (ß, ł, ø, æ, œ, đ).

    Args:
        text: A string (should already be normalized via ``normalize``).

    Returns:
        Accent-folded string with all diacritics removed.
    """
    text = text.translate(_SPECIAL_FOLDS_TABLE)
    # NFKD decomposes accented chars into base + combining mark.
    # Stripping combining marks (category "M") leaves the base character.
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")
