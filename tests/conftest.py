"""Shared test fixtures for the address classification service."""

import pytest
from fastapi.testclient import TestClient

from src.data.index import build_city_index
from src.data.loader import load_cities
from src.main import app
from src.services.pipeline import ClassificationPipeline


@pytest.fixture(scope="session")
def city_pairs():
    """Load city-country pairs once for the entire test session."""
    return load_cities()


@pytest.fixture(scope="session")
def city_index(city_pairs):
    """Build the FlashText index once for the entire test session."""
    return build_city_index(city_pairs)


@pytest.fixture(scope="session")
def pipeline(city_index):
    """Create a classification pipeline once for the entire test session."""
    nfc_proc, nfc_ctc, fold_proc, fold_ctc = city_index
    return ClassificationPipeline(nfc_proc, nfc_ctc, fold_proc, fold_ctc)


@pytest.fixture(scope="session")
def client(city_index):
    """Create a FastAPI test client with pre-loaded index data."""
    nfc_proc, nfc_ctc, fold_proc, fold_ctc = city_index
    app.state.pipeline = ClassificationPipeline(nfc_proc, nfc_ctc, fold_proc, fold_ctc)
    app.state.city_to_countries = nfc_ctc
    return TestClient(app)
