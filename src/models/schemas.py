"""Request and response schemas for the address classification API."""

from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    """Single address classification request."""

    address: str = Field(..., min_length=1, description="The address string to classify")


class ClassifyResponse(BaseModel):
    """Single address classification response."""

    address: str = Field(..., description="The original address string")
    country: str | None = Field(None, description="ISO 3166-1 alpha-2 country code, or null if unresolved")
