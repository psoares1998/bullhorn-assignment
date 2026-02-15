"""FastAPI application entry point.

Configures the app with a lifespan context manager that loads the
city index and builds the classification pipeline at startup.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import router
from src.data.index import build_city_index
from src.data.loader import load_cities
from src.services.pipeline import ClassificationPipeline

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Load data and build indexes at startup.

    Yields:
        None — control is returned to FastAPI to handle requests.
    """
    logger.info("Loading city data...")
    city_pairs = load_cities()
    logger.info("Loaded %d city-country pairs.", len(city_pairs))

    logger.info("Building FlashText indexes...")
    nfc_proc, nfc_ctc, fold_proc, fold_ctc = build_city_index(city_pairs)
    logger.info("NFC index: %d entries, folded index: %d entries.", len(nfc_ctc), len(fold_ctc))

    pipeline = ClassificationPipeline(nfc_proc, nfc_ctc, fold_proc, fold_ctc)

    app.state.pipeline = pipeline

    yield


app = FastAPI(
    title="Address Classification Service",
    description="Identifies the country an address belongs to.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
