"""Tests for the API layer (HTTP endpoints)."""


class TestClassifyEndpoint:
    """POST /classify endpoint tests."""

    def test_classify_returns_200(self, client):
        """Successful classification returns HTTP 200."""
        response = client.post("/classify", json={"address": "Mitterweg Angath"})
        assert response.status_code == 200

    def test_classify_response_schema(self, client):
        """Response contains address and country fields."""
        response = client.post("/classify", json={"address": "Mitterweg Angath"})
        data = response.json()
        assert "address" in data
        assert "country" in data

    def test_classify_preserves_original_address(self, client):
        """Response echoes back the original address string."""
        address = "FLIRSCHBERG FLIRSCH, ÖSTERREICH"
        response = client.post("/classify", json={"address": address})
        assert response.json()["address"] == address

    def test_classify_returns_country_name(self, client):
        """Known address returns the full country name."""
        response = client.post("/classify", json={"address": "Mitterweg Angath"})
        assert response.json()["country"] == "Austria"

    def test_classify_empty_address_returns_422(self, client):
        """Empty address string returns HTTP 422 validation error."""
        response = client.post("/classify", json={"address": ""})
        assert response.status_code == 422

    def test_classify_missing_address_returns_422(self, client):
        """Missing address field returns HTTP 422 validation error."""
        response = client.post("/classify", json={})
        assert response.status_code == 422

    def test_classify_unresolved_returns_null(self, client):
        """Unresolvable address returns null country."""
        response = client.post("/classify", json={"address": "qxzjk wvnmp"})
        assert response.json()["country"] is None
