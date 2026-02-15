"""Layered Classification Pipeline — L0 through L6.

Classifies an address to its country using libpostal for address
parsing and a sequence of signal extraction layers for classification.
"""

import re

from flashtext import KeywordProcessor
from postal.parser import parse_address

from src.services.normalizer import accent_fold, normalize

# ---------------------------------------------------------------------------
# L2 — Country Name Detection
# ---------------------------------------------------------------------------
# Maps country name variants (in accent-folded form) to ISO country codes.
_COUNTRY_NAMES: dict[str, str] = {
    # AT
    "austria": "AT",
    "osterreich": "AT",
    "republik osterreich": "AT",
    # BE
    "belgium": "BE",
    "belgique": "BE",
    "belgie": "BE",
    "belgien": "BE",
    # CZ
    "czech republic": "CZ",
    "czechia": "CZ",
    "ceska republika": "CZ",
    "cesko": "CZ",
    # DE
    "germany": "DE",
    "deutschland": "DE",
    "bundesrepublik deutschland": "DE",
    # EE
    "estonia": "EE",
    "eesti": "EE",
    # FR
    "france": "FR",
    # IT
    "italy": "IT",
    "italia": "IT",
    # LU
    "luxembourg": "LU",
    "luxemburg": "LU",
    "letzebuerg": "LU",
    # NL
    "netherlands": "NL",
    "nederland": "NL",
    "the netherlands": "NL",
    # PL
    "poland": "PL",
    "polska": "PL",
    # PT
    "portugal": "PT",
    # RO
    "romania": "RO",
    # SE
    "sweden": "SE",
    "sverige": "SE",
    # SI
    "slovenia": "SI",
    "slovenija": "SI",
    # SK
    "slovakia": "SK",
    "slovensko": "SK",
    "slovenska republika": "SK",
}

# Pre-compiled regexes with word boundaries, longest-first.
_COUNTRY_NAME_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b" + re.escape(name) + r"\b"), code)
    for name, code in sorted(_COUNTRY_NAMES.items(), key=lambda x: -len(x[0]))
]


# ---------------------------------------------------------------------------
# L3 — Postal Code Pattern Detection
# ---------------------------------------------------------------------------
# Ordered by specificity: unique formats first, ambiguous formats last.
_POSTAL_PATTERNS: list[tuple[re.Pattern[str], str | set[str]]] = [
    # PL: NN-NNN (e.g., "01-234")
    (re.compile(r"\b\d{2}-\d{3}\b"), "PL"),
    # PT: NNNN-NNN (e.g., "1234-567")
    (re.compile(r"\b\d{4}-\d{3}\b"), "PT"),
    # SE: NNN NN (with space) — unambiguous
    (re.compile(r"\b\d{3}\s\d{2}\b"), "SE"),
    # 5-digit: FR, DE, IT, SE (ambiguous — SE postal without space looks like 5 digits)
    (re.compile(r"\b\d{5}\b"), {"FR", "DE", "IT", "SE"}),
    # 4-digit: BE, AT, LU, SI (ambiguous)
    (re.compile(r"\b\d{4}\b"), {"BE", "AT", "LU", "SI"}),
]

# ---------------------------------------------------------------------------
# L5 — Linguistic Feature Detection
# ---------------------------------------------------------------------------
# Maps language-specific address terms to their possible countries.
_LINGUISTIC_TERMS: dict[str, set[str]] = {
    # German
    "strasse": {"DE", "AT"},
    "stra\u00dfe": {"DE", "AT"},
    "gasse": {"DE", "AT"},
    "platz": {"DE", "AT"},
    "weg": {"DE", "AT"},
    # Dutch
    "straat": {"NL", "BE"},
    "plein": {"NL", "BE"},
    "laan": {"NL", "BE"},
    "kade": {"NL", "BE"},
    "singel": {"NL", "BE"},
    "dreef": {"NL", "BE"},
    "gracht": {"NL"},
    # French
    "rue": {"FR"},
    "boulevard": {"FR"},
    "chemin": {"FR"},
    "place": {"FR"},
    "impasse": {"FR"},
    "allee": {"FR", "DE", "AT"},
    # Portuguese
    "rua": {"PT"},
    "avenida": {"PT"},
    "travessa": {"PT"},
    "praca": {"PT"},
    "largo": {"PT"},
    "beco": {"PT"},
    "estrada": {"PT"},
    # Italian
    "via": {"IT"},
    "viale": {"IT"},
    "piazza": {"IT"},
    "corso": {"IT"},
    "vicolo": {"IT"},
    "piazzale": {"IT"},
    # Polish / Slovenian / Slovak (shared term)
    "ulica": {"PL", "SK", "SI"},
    "aleja": {"PL"},
    "plac": {"PL"},
    "osiedle": {"PL"},
    # Czech
    "ulice": {"CZ"},
    "namesti": {"CZ"},
    "trida": {"CZ"},
    # Estonian
    "tanav": {"EE"},
    "tee": {"EE"},
    "vald": {"EE"},
    "kula": {"EE"},
    "linn": {"EE"},
    "alevik": {"EE"},
    "maakond": {"EE"},
    # Swedish
    "gatan": {"SE"},
    "vagen": {"SE"},
    "allen": {"SE"},
    "stigen": {"SE"},
    "torget": {"SE"},
    # Slovenian
    "cesta": {"SI"},
    "trg": {"SI"},
    # Romanian
    "bulevard": {"RO"},
    "calea": {"RO"},
    "soseaua": {"RO"},
    # Slovak
    "namestie": {"SK"},
}

# Pre-sort longest-first to match multi-word terms before single-word.
_LINGUISTIC_SORTED: list[tuple[str, set[str]]] = sorted(_LINGUISTIC_TERMS.items(), key=lambda x: -len(x[0]))


class ClassificationPipeline:
    """Layered address classification pipeline.

    Uses libpostal for address parsing followed by signal extraction
    layers (country name, postal code, city matching, linguistic
    features) and a voting system for final classification.
    """

    def __init__(
        self,
        nfc_processor: KeywordProcessor,
        nfc_city_to_countries: dict[str, set[str]],
        folded_processor: KeywordProcessor,
        folded_city_to_countries: dict[str, set[str]],
    ) -> None:
        """Initialize the pipeline with pre-built index data.

        Args:
            nfc_processor: FlashText index with NFC (accented) city names.
            nfc_city_to_countries: NFC city name to country codes.
            folded_processor: FlashText index with accent-folded city names.
            folded_city_to_countries: Folded city name to country codes.
        """
        self._nfc_processor = nfc_processor
        self._nfc_city_to_countries = nfc_city_to_countries
        self._folded_processor = folded_processor
        self._folded_city_to_countries = folded_city_to_countries

    def classify(self, raw_address: str) -> str | None:
        """Classify an address to its country code.

        Runs the address through layers L0-L6:
        L0: Normalization
        L1: Address parsing (libpostal)
        L2: Country name detection (short-circuit)
        L3: Postal code detection
        L4: City matching
        L5: Linguistic features
        L6: Voting

        Args:
            raw_address: The raw address string.

        Returns:
            ISO 3166-1 alpha-2 country code, or None if unresolved.
        """
        if not raw_address or not raw_address.strip():
            return None

        # L0 — Normalization
        normalized = normalize(raw_address)

        # L1 — Address Parsing
        components = self._parse_address(normalized)

        # L2 — Country Name Detection (short-circuit)
        if components.get("country"):
            country_text = components["country"]
            country = self._detect_country_name(country_text)
            if not country:
                country = self._detect_country_name(accent_fold(country_text))
            if country:
                return country

        # L3 — City Matching
        # 1. NFC exact, 2. folded fallback, 3. last road word + city
        city_matches: list[tuple[str, int, set[str]]] = []
        for label in ("city", "state_district"):
            if components.get(label):
                text = normalize(components[label])
                # Step 1: NFC exact
                matches = self._match_cities(text, use_folded=False)
                # Step 2: folded fallback
                if not matches:
                    folded = accent_fold(text)
                    matches = self._match_cities(folded, use_folded=True)
                # Step 3: prepend last word of road to city
                if not matches and components.get("road"):
                    road_words = components["road"].strip().split()
                    if road_words:
                        extended = normalize(road_words[-1] + " " + components[label])
                        matches = self._match_cities(extended, use_folded=False)
                        if not matches:
                            matches = self._match_cities(accent_fold(extended), use_folded=True)
                city_matches.extend(matches)

        # If city matching is unambiguous (all matches point to 1 country), return it.
        if city_matches:
            all_city_countries: set[str] = set()
            for _, _, countries in city_matches:
                all_city_countries.update(countries)
            if len(all_city_countries) == 1:
                return next(iter(all_city_countries))

        # L4 — Postal Code Detection
        postal_result = None
        if components.get("postcode"):
            postal_result = self._detect_postal_code(components["postcode"])

        # L5 — Linguistic Features (original first, folded fallback)
        linguistic_countries: set[str] = set()
        road_text = components.get("road", "")
        if road_text:
            linguistic_countries = self._detect_linguistic_features(road_text)
            if not linguistic_countries:
                folded_road = accent_fold(road_text)
                if folded_road != road_text:
                    linguistic_countries = self._detect_linguistic_features(folded_road)

        # L6 — Voting (city ambiguous or not found, use all signals)
        return self._vote(postal_result, city_matches, linguistic_countries)

    def _parse_address(self, text: str) -> dict[str, str]:
        """L1: Parse address into structural components using libpostal.

        Args:
            text: Normalized address string.

        Returns:
            Dict mapping component labels to their values.
        """
        components: dict[str, str] = {}
        for value, label in parse_address(text):
            if label in ("city", "road", "postcode", "country", "state", "state_district"):
                if label in components:
                    components[label] += " " + value
                else:
                    components[label] = value
        return components

    def _detect_country_name(self, text: str) -> str | None:
        """L2: Detect explicit country names in the parsed country component.

        Args:
            text: Accent-folded country component from libpostal.

        Returns:
            Country code if a country name is found, None otherwise.
        """
        for pattern, code in _COUNTRY_NAME_PATTERNS:
            if pattern.search(text):
                return code
        return None

    def _detect_postal_code(self, text: str) -> str | set[str] | None:
        """L3: Detect postal code patterns in the parsed postcode component.

        Args:
            text: Postcode component from libpostal.

        Returns:
            A single country code string, a set of candidate codes,
            or None if no postal code pattern matches.
        """
        for pattern, result in _POSTAL_PATTERNS:
            if pattern.search(text):
                return result
        return None

    def _match_cities(self, text: str, *, use_folded: bool = False) -> list[tuple[str, int, set[str]]]:
        """L3: Extract city names from the parsed city component.

        Uses the NFC index by default (precise matching). When
        use_folded is True, uses the accent-folded index (fallback).

        Args:
            text: City text to search.
            use_folded: If True, use the folded index instead of NFC.

        Returns:
            List of (city_key, end_position, countries) tuples.
        """
        processor = self._folded_processor if use_folded else self._nfc_processor
        city_to_countries = self._folded_city_to_countries if use_folded else self._nfc_city_to_countries

        matches: list[tuple[str, int, set[str]]] = []
        for city_key, _start, end in processor.extract_keywords(text, span_info=True):
            city_countries = city_to_countries.get(city_key, set())
            matches.append((city_key, end, city_countries))
        matches.sort(key=lambda m: m[1])
        return matches

    def _detect_linguistic_features(self, text: str) -> set[str]:
        """L5: Detect language-specific address terms in the road component.

        Checks both exact word matches (e.g., "rue", "via") and suffix
        matches (e.g., "wiesenstraße" ends with "straße") to handle
        Germanic languages where the street type is a compound suffix.

        Args:
            text: Road component from libpostal.

        Returns:
            Set of country codes suggested by linguistic features.
        """
        countries: set[str] = set()
        words = text.split()
        matched_words: set[str] = set()
        # Exact word match first.
        word_set = set(words)
        for term, term_countries in _LINGUISTIC_SORTED:
            if term in word_set:
                countries.update(term_countries)
                matched_words.add(term)
        # Suffix match for remaining words.
        for word in words:
            if word in matched_words:
                continue
            for term, term_countries in _LINGUISTIC_SORTED:
                if word.endswith(term) and word != term:
                    countries.update(term_countries)
                    break
        return countries

    def _vote(
        self,
        postal_result: str | set[str] | None,
        city_matches: list[tuple[str, int, set[str]]],
        linguistic_countries: set[str],
    ) -> str | None:
        """L6: Vote across all signals and return the winner.

        Each city match gives +1 vote per country it supports.
        The postal code gives +1 vote per country in its set.
        Each linguistic term gives +1 vote per country.
        The country with the most votes wins. Ties return None.

        Args:
            postal_result: Postal code detection result.
            city_matches: City matches from L4.
            linguistic_countries: Countries from L5.

        Returns:
            Country code or None.
        """
        votes: dict[str, int] = {}

        # City votes: each match gives +1 per country.
        for _, _, countries in city_matches:
            for country in countries:
                votes[country] = votes.get(country, 0) + 1

        # Postal vote: +1 per country in the set.
        postal_set: set[str] = (
            {postal_result}
            if isinstance(postal_result, str)
            else postal_result
            if isinstance(postal_result, set)
            else set()
        )
        for country in postal_set:
            votes[country] = votes.get(country, 0) + 1

        # Linguistic vote: +1 per country.
        for country in linguistic_countries:
            votes[country] = votes.get(country, 0) + 1

        if not votes:
            return None

        # Country with the most votes wins. Ties return None.
        max_votes = max(votes.values())
        winners = [c for c, v in votes.items() if v == max_votes]

        if len(winners) == 1:
            return winners[0]

        return None
