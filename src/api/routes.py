"""API route definitions for the address classification service."""

from fastapi import APIRouter, Request

from src.models.schemas import ClassifyRequest, ClassifyResponse

router = APIRouter()

_COUNTRY_NAMES: dict[str, str] = {
    "AT": "Austria",
    "BE": "Belgium",
    "CZ": "Czech Republic",
    "DE": "Germany",
    "EE": "Estonia",
    "FR": "France",
    "IT": "Italy",
    "LU": "Luxembourg",
    "NL": "Netherlands",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SE": "Sweden",
    "SI": "Slovenia",
    "SK": "Slovakia",
}


@router.post("/classify", response_model=ClassifyResponse)
def classify_address(body: ClassifyRequest, request: Request) -> ClassifyResponse:
    """Classify a single address to its country.

    Args:
        body: Request body containing the address string.
        request: FastAPI request object (provides access to app state).

    Returns:
        Classification result with the address and its country name.
    """
    pipeline = request.app.state.pipeline
    code = pipeline.classify(body.address)
    country = _COUNTRY_NAMES.get(code, code) if code else None
    return ClassifyResponse(address=body.address, country=country)
