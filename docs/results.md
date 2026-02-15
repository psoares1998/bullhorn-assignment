# Assignment Results

## Source Code

The service is structured with a clear separation of concerns:

- **`src/api/`** — Request logic: HTTP endpoint definition and response formatting
- **`src/services/`** — Business logic: classification pipeline and text normalization
- **`src/data/`** — Data logic: dataset loading and city index construction
- **`src/models/`** — Request/response schemas (Pydantic)

Entry point: `src/main.py` — FastAPI application with startup lifecycle that loads data and builds indexes.

## Data and Extensibility

The dataset contains two files:

- `cities.jsonl` — 77,481 city-country pairs used to build the classification index (loaded at startup)
- `addresses.jsonl` — 595,496 labeled address-country pairs used exclusively for evaluation and validation

Only `cities.jsonl` is required at runtime. `addresses.jsonl` is used by the evaluation scripts to measure accuracy.

## Adding a New Country

1. Add city entries to `cities.jsonl` (city name + country code)
2. Add country name variants to `_COUNTRY_NAMES` in `src/services/pipeline.py`
3. Add a postal code regex to `_POSTAL_PATTERNS` if the format is distinctive
4. Add language-specific street terms to `_LINGUISTIC_TERMS`
5. Add the country name mapping to `_COUNTRY_NAMES` in `src/api/routes.py`

No code changes to the pipeline logic, no retraining required.

## Approach and Limitations

The service uses a layered classification pipeline that parses each address into structural components (via libpostal) and extracts signals through specialized layers — country name detection, city matching, postal code patterns, and linguistic features. When no single layer resolves the country, a voting system combines all signals. Full details in [solution-approach.md](solution-approach.md).

The rationale for choosing this approach over ML or LLM alternatives is documented in [approach-comparison.md](approach-comparison.md).

An exploratory data analysis of the dataset, including the identification and filtering of unclassifiable addresses, is documented in [eda.md](eda.md).

**Limitations:**

- If a city is not in `cities.jsonl` and no other signal is present, the address will not be resolved
- Addresses where libpostal does not correctly extract the city component (common in SI, EE, PT) may go unresolved
- 4-digit and 5-digit postal codes overlap across several countries and cannot resolve the country alone
- Typos or misspellings in city names will not match the index — there is no fuzzy matching

**Possible improvements:**

- Fuzzy matching for city names to handle typos (e.g., "Insbruck" matching "Innsbruck" via edit distance)
- ML fallback layer for addresses the pipeline cannot resolve
- Postal code range database for precise resolution of ambiguous numeric postal codes
- Enriching the city index with additional data sources (e.g., GeoNames) to improve coverage

## Running in Production

The service is containerized with Docker:

```bash
docker compose up --build
```

This builds and starts the service on port 8000. The container is self-contained — all data and dependencies are bundled in the image, no external API calls are made at runtime.

For scaling, the service is stateless after startup (all data is loaded into memory). Multiple container replicas can run behind a load balancer without coordination.

## How to Run

Start the service with Docker:

```bash
docker compose up --build
```

Once running, there are two ways to interact with the service:

**Option 1 — Swagger UI:** Open `http://localhost:8000/docs` in a browser. This provides an interactive interface where you can type an address directly and see the response, without needing any additional tools.

**Option 2 — curl / HTTP client:**

```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"address": "Nieuwendammerkade 26A-5, Amsterdam"}'
```

Response:
```json
{"address": "Nieuwendammerkade 26A-5, Amsterdam", "country": "Netherlands"}
```
