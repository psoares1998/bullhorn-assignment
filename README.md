# Address Classification Service

HTTP service that identifies the country an address belongs to.

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

## Project Structure

```
├── docs/
│   ├── eda.md                     # Exploratory data analysis
│   ├── results.md                 # Assignment results and deliverables
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

## Documentation

- [Assignment Results](docs/results.md) — deliverables, limitations, how to run and extend
- [Solution Approach](docs/solution-approach.md) — pipeline architecture and layer details
- [Approach Comparison](docs/approach-comparison.md) — why a pipeline over ML/LLM
- [Exploratory Data Analysis](docs/eda.md) — dataset analysis and filtering rationale
