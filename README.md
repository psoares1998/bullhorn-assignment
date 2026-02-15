# Address Classification Service

HTTP service that identifies the country an address belongs to.

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

### Local (requires WSL/Linux — libpostal does not run on Windows)

```bash
pip install -e ".[dev]"
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

The service starts at `http://localhost:8000`.

## API Usage

```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"address": "Nieuwendammerkade 26A-5, Amsterdam"}'
```

Response:
```json
{"address": "Nieuwendammerkade 26A-5, Amsterdam", "country": "Netherlands"}
```

Interactive API docs available at `http://localhost:8000/docs`.

## Running Tests

```bash
pytest
```

## Evaluation

Run the pipeline against the full labeled dataset:

```bash
python scripts/evaluation/evaluate.py
```

## Project Structure

```
├── docs/
│   ├── eda.md                     # Exploratory data analysis
│   ├── solution-approach.md       # Pipeline architecture (L0-L6)
│   └── approach-comparison.md     # Approach comparison and rationale
├── src/
│   ├── api/                       # Request logic (HTTP handlers)
│   ├── services/                  # Business logic (classification pipeline)
│   ├── data/                      # Data logic (loading, indexing)
│   └── models/                    # Request/response schemas
├── scripts/
│   ├── analysis/                  # EDA and data analysis scripts
│   ├── evaluation/                # Accuracy evaluation and misclassification scripts
│   ├── data/                      # Dataset preparation (filtering)
│   └── output/                    # Generated output files
├── tests/                         # Unit and integration tests
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## How to Add a New Country

1. Add city entries to `cities.jsonl`
2. Add country name variants to `_COUNTRY_NAMES` in `src/services/pipeline.py`
3. Add a postal code regex to `_POSTAL_PATTERNS` if the format is distinctive
4. Add linguistic terms to `_LINGUISTIC_TERMS` for the country's language

No retraining or code changes to the pipeline logic required.

See [docs/solution-approach.md](docs/solution-approach.md) for full details.
