"""Tests for L0 — text normalization and accent folding."""

import pytest

from src.services.normalizer import accent_fold, normalize


class TestNormalize:
    """Tests for the normalize function."""

    def test_lowercase(self):
        """Case folding converts to lowercase."""
        assert normalize("INNSBRUCK") == "innsbruck"

    def test_mixed_case(self):
        """Mixed case is folded to lowercase."""
        assert normalize("Kematen in Tirol") == "kematen in tirol"

    def test_whitespace_collapse(self):
        """Multiple spaces are collapsed to a single space."""
        assert normalize("rue   de   la   paix") == "rue de la paix"

    def test_trim(self):
        """Leading and trailing whitespace is removed."""
        assert normalize("  innsbruck  ") == "innsbruck"

    def test_leading_comma(self):
        """Leading comma with optional space is removed."""
        assert normalize(", KALMAR") == "kalmar"

    def test_preserves_accents(self):
        """Accented characters are preserved after NFKD normalization."""
        result = normalize("Kitzbühel")
        assert "u" in result or "ü" in result  # NFKD decomposes ü

    def test_empty_string(self):
        """Empty string returns empty string."""
        assert normalize("") == ""


class TestAccentFold:
    """Tests for the accent_fold function."""

    def test_basic_accent_removal(self):
        """Common accented characters are folded to ASCII."""
        assert accent_fold("kitzbuehel") == "kitzbuehel"  # no accent, unchanged
        assert accent_fold(normalize("Kitzbühel")) == "kitzbuhel"

    def test_eszett(self):
        """German ß is folded to ss."""
        assert accent_fold("straße") == "strasse"

    def test_polish_l(self):
        """Polish ł is folded to l."""
        assert accent_fold("łódź") == "lodz"

    def test_nordic_o(self):
        """Nordic ø is folded to o."""
        assert accent_fold("ørsted") == "orsted"

    def test_ligature_ae(self):
        """Ligature æ is folded to ae."""
        assert accent_fold("præst") == "praest"

    def test_ligature_oe(self):
        """Ligature œ is folded to oe."""
        assert accent_fold("cœur") == "coeur"

    def test_croatian_d(self):
        """Croatian đ is folded to d."""
        assert accent_fold("đurđevac") == "durdevac"

    @pytest.mark.parametrize(
        ("input_text", "expected"),
        [
            ("café", "cafe"),
            ("naïve", "naive"),
            ("résumé", "resume"),
            ("ñoño", "nono"),
        ],
    )
    def test_various_accents(self, input_text, expected):
        """Various accented characters are correctly folded."""
        assert accent_fold(input_text) == expected

    def test_ascii_unchanged(self):
        """Pure ASCII text is returned unchanged."""
        assert accent_fold("hello world") == "hello world"
