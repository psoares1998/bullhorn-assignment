"""Tests for the classification pipeline (L1-L6)."""

import pytest


class TestCountryNameDetection:
    """L1 — Country name detection."""

    @pytest.mark.parametrize(
        ("address", "expected"),
        [
            ("josef-franz-huter-straße 72 6020, innsbruck, austria", "AT"),
            ("FLIRSCHBERG FLIRSCH, ÖSTERREICH", "AT"),
            ("Rue de Rivoli, Paris, France", "FR"),
            ("Hauptstraße 1, Berlin, Deutschland", "DE"),
            ("Kungsgatan 5, Stockholm, Sverige", "SE"),
            ("Rua Augusta, Lisboa, Portugal", "PT"),
            ("Krakowska 1, Warszawa, Polska", "PL"),
            ("Strada Victoriei, Bucuresti, Romania", "RO"),
        ],
    )
    def test_explicit_country_name(self, pipeline, address, expected):
        """Addresses with explicit country names are resolved by L1."""
        assert pipeline.classify(address) == expected


class TestPostalCodeDetection:
    """L2 — Postal code pattern detection."""

    def test_polish_postal_code(self, pipeline):
        """PL postal code format (NN-NNN) is uniquely detected."""
        assert pipeline.classify("Marszalkowska 1, 00-001") == "PL"

    def test_portuguese_postal_code(self, pipeline):
        """PT postal code format (NNNN-NNN) is uniquely detected."""
        assert pipeline.classify("Rua Augusta 100, 1100-053") == "PT"

    def test_swedish_postal_code(self, pipeline):
        """SE postal code format (NNN NN) is detected."""
        assert pipeline.classify("Kungsgatan 1, 111 43") == "SE"


class TestCityMatching:
    """L3 — City name matching via FlashText."""

    def test_single_word_city(self, pipeline):
        """Single-word city names are matched."""
        assert pipeline.classify("Mitterweg Angath") == "AT"

    def test_multi_word_city(self, pipeline):
        """Multi-word city names are matched as a single keyword."""
        result = pipeline.classify("Dorfstraße 5, Kematen in Tirol")
        assert result == "AT"

    def test_case_insensitive(self, pipeline):
        """City matching works regardless of case."""
        assert pipeline.classify("FULPMES") == "AT"
        assert pipeline.classify("fulpmes") == "AT"

    def test_word_boundary_no_false_positive(self, pipeline):
        """FlashText does not match substrings inside larger words."""
        # "rum" should not be falsely matched inside "forum"
        result = pipeline.classify("Forum 1, Brno")
        assert result == "CZ"

    def test_accented_city(self, pipeline):
        """Accented city names are matched via dual-index."""
        result = pipeline.classify("Hauptplatz 1, Kitzbühel")
        assert result == "AT"


class TestLinguisticFeatures:
    """L4 — Linguistic feature detection as tiebreaker."""

    def test_dutch_street_term(self, pipeline):
        """Dutch street terms help resolve NL/BE ambiguity."""
        result = pipeline.classify("Prinsengracht 200, Amsterdam")
        assert result == "NL"

    def test_portuguese_street_term(self, pipeline):
        """Portuguese street terms indicate PT."""
        result = pipeline.classify("travessa do almada 10")
        assert result == "PT"


class TestSuffixMatching:
    """L5 — Suffix matching for compound street names."""

    def test_german_compound_strasse(self, pipeline):
        """Germanic compound suffix 'straße' is detected in compound words."""
        result = pipeline.classify("wiesenstraße morsbach")
        assert result == "DE"

    def test_german_compound_weg(self, pipeline):
        """Germanic compound suffix 'weg' is detected in compound words."""
        result = pipeline.classify("feldweg innsbruck")
        assert result == "AT"


class TestAccentFallback:
    """Accent-folded fallback matching."""

    def test_folded_city_match(self, pipeline):
        """City with accents is matched when input has no accents."""
        result = pipeline.classify("GROSSDORF 49 KALS AM GROSSGLOCKNER")
        assert result == "AT"

    def test_parentheses_in_city(self, pipeline):
        """City names with parentheses are matched after normalization."""
        result = pipeline.classify("hennef (sieg)")
        assert result == "DE"


class TestVoting:
    """L6 — Voting with multiple signals."""

    def test_city_and_linguistic_agree(self, pipeline):
        """Multiple signals pointing to the same country resolve correctly."""
        result = pipeline.classify("rua das flores 289 porto")
        assert result == "PT"

    def test_linguistic_only(self, pipeline):
        """Address with only a linguistic signal resolves via voting."""
        result = pipeline.classify("rua das flores")
        assert result == "PT"


class TestEdgeCases:
    """Edge cases and fallback behavior."""

    def test_empty_string(self, pipeline):
        """Empty string returns None."""
        assert pipeline.classify("") is None

    def test_whitespace_only(self, pipeline):
        """Whitespace-only string returns None."""
        assert pipeline.classify("   ") is None

    def test_unknown_address(self, pipeline):
        """Completely unrecognizable address returns None."""
        assert pipeline.classify("qxzjk wvnmp") is None
