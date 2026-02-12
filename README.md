# Address Classification Service

HTTP service that identifies the country an address belongs to.

## Project Structure

```
bullhorn-assignment/
├── address_classification_dataset/   # Original dataset (OpenAddresses)
│   └── dataset/
│       ├── addresses.jsonl           # 595K labeled address-country pairs
│       └── cities.jsonl              # 77K city-country pairs
├── data-processing/                  # Data exploration and analysis
│   ├── docs/
│   │   └── eda.md                    # Exploratory data analysis
│   └── scripts/                      # EDA and data processing scripts
├── src/
│   ├── api/                          # Request logic (HTTP handlers, routing)
│   ├── services/                     # Business logic (classification pipeline)
│   ├── data/                         # Data logic (loading, indexing, lookups)
│   └── models/                       # Data models and schemas
├── tests/                            # Unit and integration tests
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Architecture

The service follows a three-layer separation:

- **API layer** (`src/api/`) — HTTP request handling, input validation, response formatting
- **Service layer** (`src/services/`) — Address classification pipeline and business rules
- **Data layer** (`src/data/`) — Dataset loading, index construction, and lookups
