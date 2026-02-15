# Exploratory Data Analysis — Address Classification Dataset

## 1. Dataset Overview

Two JSONL files:

| File | Records | Fields | Purpose |
|---|---|---|---|
| `addresses.jsonl` | 595,496 | `address`, `country` | Labeled address-country pairs for validation |
| `cities.jsonl` | 77,481 | `city`, `country` | City-to-country index for building the classifier |

Country codes use **ISO 3166-1 alpha-2** format. Both files cover the same **15 European countries**.

### Distribution by Country

| Country | ISO | Addresses | % | Cities |
|---|---|---|---|---|
| France | FR | 257,025 | 43.16% | 32,650 |
| Netherlands | NL | 90,589 | 15.21% | 2,426 |
| Germany | DE | 52,647 | 8.84% | 1,853 |
| Poland | PL | 40,658 | 6.83% | 5,670 |
| Belgium | BE | 39,338 | 6.61% | 340 |
| Portugal | PT | 33,168 | 5.57% | 18,299 |
| Italy | IT | 33,093 | 5.56% | 3,798 |
| Czech Republic | CZ | 19,110 | 3.21% | 2,996 |
| Estonia | EE | 11,639 | 1.95% | 1,191 |
| Slovakia | SK | 5,839 | 0.98% | 1,940 |
| Slovenia | SI | 5,542 | 0.93% | 5,302 |
| Sweden | SE | 3,101 | 0.52% | 194 |
| Austria | AT | 1,884 | 0.32% | 279 |
| Luxembourg | LU | 1,591 | 0.27% | 538 |
| Romania | RO | 272 | 0.05% | 5 |

**Notable imbalances:** France alone accounts for 43% of all addresses. Romania has only 272 addresses and 5 cities — minimal coverage. Belgium has 39K addresses but only 340 cities in the index.

---

## 2. Address Format Patterns

### 2.1 Case Distribution

Addresses are evenly split across casing styles — normalization is mandatory.

| Style | Count | % |
|---|---|---|
| Mixed Case | 199,103 | 33.4% |
| All Lowercase | 198,385 | 33.3% |
| All Uppercase | 198,008 | 33.3% |

### 2.2 Explicit Country Name

~**29% of addresses** contain the country name (e.g., "austria", "ÖSTERREICH", "nederland"). This is a high-confidence signal when present, but absent in ~71% of cases.

Variants found include native names: `ÖSTERREICH`, `nederland`, `deutschland`, `sverige`, `eesti`, `slovenija`, `česko`, `italia`, `belgique`.

### 2.3 Postal Code Patterns

Several countries have **unique postal code formats** that serve as strong classification signals:

| Country | Format | Example | Coverage | Uniqueness |
|---|---|---|---|---|
| NL | `NNNNLL` | `4529Gs` | 22,137 / 90,589 (24.4%) | Unique globally |
| PL | `NN-NNN` | `00-000` | 10,007 / 40,658 (24.6%) | Unique in dataset |
| SE | `NNN NN` | `441 56` | 576 / 3,101 (18.6%) | Distinguishable |
| PT | `NNNN-NNN` | `2345-678` | Subset of PT addresses | Unique format |
| FR, DE, IT | `NNNNN` (5-digit) | `75001` | ~25-27% each | Ambiguous — ranges overlap |
| BE, AT | `NNNN` (4-digit) | `1800`, `6020` | ~25% each | Ambiguous — ranges overlap |
| CZ, SK | `NNN NN` | `110 00` | ~25% each | Similar to SE |

**Key insight:** NL and PL postal codes are highly distinctive and can resolve the country with near certainty. For 5-digit and 4-digit codes, postal code ranges may help but are not fully reliable on their own.

---

## 3. City Index Analysis

### 3.1 Shared City Names

**291 city names** appear in 2 or more countries (case-insensitive, preserving accents) — 14 in 3 countries and 277 in 2 countries. This is expected given the geographic proximity of the 15 European countries in the dataset. Examples:

| City | Countries |
|---|---|
| costa | FR, IT, PT |
| halle | BE, DE, NL |
| most | CZ, SI |
| pavia | IT, PT |
| bach | AT, FR |
| lagos | FR, PT |
| brakel | BE, DE, NL |
| strassen | AT, LU |

A city name alone is not always sufficient to determine the country. When the address contains additional context — a postal code, a street name, or the country name itself — the classifier can use those signals to disambiguate. 

**However, when the address contains **only** a shared city name, classification becomes impossible without guessing.**

### 3.2 Other Characteristics

- **Multi-word cities (25.7%):** 19,910 city names contain multiple words (e.g., `Polling in Tirol`, `Going am Wilden Kaiser`, `Sas Van Gent`). The matching strategy must support multi-token lookup.
- **Short city names (1-3 chars):** Names like `Y` (FR), `Erl` (AT), or `Col` (SI) can match inside longer words if matching is not boundary-aware.
- **Non-ASCII characters (25.3%):** 19,625 city names contain diacritics (`ö`, `ü`, `ß`, `ç`, `ã`, `ń`, `ř`, `š`, etc.). Addresses may use the accented form, the unaccented form, or a mix of both.

### 3.3 Unclassifiable Addresses — Dataset Filtering

Cross-referencing the 291 shared city names with `addresses.jsonl` revealed **1,722 addresses** that consist of **only** a shared city name with no additional context. Two patterns were found:

- `"lagos"` — labeled PT, but also exists in FR
- `"HAGEN"` — labeled LU, but also exists in DE and NL
- `"mechelen"` — labeled BE, but also exists in NL
- `"LIPOVEC LIPOVEC"` — labeled SI, but `lipovec` also exists in CZ and SK
- `"trnovo, trnovo"` — labeled SI, but `trnovo` also exists in SK

**In all cases, the reason for removal is the same: the city name belongs to multiple countries, and the address provides no other signal to determine which one is correct.** Whether the city appears once or is repeated with punctuation variations, the ambiguity remains.

Any classifier that returns the "correct" country for these addresses would be guessing, not classifying. Including them in the evaluation set would penalize a classifier for being honest about uncertainty (returning `None`) and reward one that guesses randomly. This contradicts the design principle of preferring no answer over an unreliable answer.

---

## 4. Filtered Dataset

Based on the analysis in section 3.3, we created a filtered evaluation dataset (`addresses_filtered.jsonl`) with the 1,722 unclassifiable entries removed:

| | Original | Filtered | Removed |
|---|---|---|---|
| Total addresses | 595,496 | 593,774 | 1,722 |
| % removed | — | — | 0.29% |

The removal represents less than 0.3% of the dataset and does not affect the country distribution in any meaningful way. The filtered dataset is used for all evaluation runs. The full list of removed addresses is available in `addresses_removed.txt`.
