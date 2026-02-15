# Solution Approach — Layered Classification Pipeline

## Overview

The service classifies addresses to their corresponding country using a **layered classification pipeline**. The address is first parsed into structural components using libpostal, then each component is analyzed by a specialized layer that extracts a different type of signal. The pipeline uses a voting system to combine signals when no single layer resolves the country with certainty.

## Pipeline Architecture

```
                         ┌──────────────┐
                         │   Raw Input   │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                    L0   │ Normalization │
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                    L1   │ Parsing       │  (libpostal → road, city, postcode, country)
                         └──────┬───────┘
                                │
                         ┌──────▼───────┐
                    L2   │ Country Name  │──── match ──── return country
                         └──────┬───────┘
                                │ no match
                         ┌──────▼───────┐
                    L3   │ City Matching │──── unambiguous ──── return country
                         └──────┬───────┘
                                │ ambiguous / no match
                         ┌──────▼───────┐
                    L4   │ Postal Code   │─┐
                         └──────────────┘  │
                         ┌──────────────┐  │
                    L5   │ Linguistic    │─┤   signals
                         └──────────────┘  │
                                           │
                         ┌──────▼───────┐
                    L6   │   Voting      │──── most votes wins / tie → null
                         └──────────────┘
```

L2 and L3 can short-circuit the pipeline when they produce a high-confidence result. When they don't, all remaining signals feed into L6 for a vote.

## Layer Details

### L0 — Normalization

Prepares the raw address for consistent matching: lowercase, Unicode NFC normalization, parentheses removal, whitespace collapse, and leading comma removal.

Applied both at startup (city index) and per request (incoming addresses).

### L1 — Address Parsing (libpostal)

Parses the normalized address into structural components using libpostal's `parse_address`. Extracts: `road`, `city`, `postcode`, `country`, `state_district`.

This is what allows each subsequent layer to analyze only the relevant part of the address — postal code patterns run on the postcode component, city matching on the city component, linguistic features on the road component. Without this separation, a house number like `10-133` could falsely match a Polish postal code pattern, or a street name like `r centro` could match a city name.

### L2 — Country Name Detection

Checks the parsed `country` component for explicit country names or variants (e.g., "austria", "osterreich", "nederland"). Uses ~40 pre-compiled regex patterns with word boundaries, longest-first.

If a country name is found, the pipeline returns immediately. Tries the original text first, then an accent-folded version as fallback.

### L3 — City Matching (FlashText)

Searches for city names from the 77K-entry index within the parsed `city` and `state_district` components.

**Dual index:** Two separate FlashText processors are built at startup — one with NFC (accented) city names and one with accent-folded names. This prevents cross-contamination where cities like "Lipa" (SI) and "Lípa" (CZ) would collide in a single folded index.

**3-step matching per component:**
1. NFC exact match (precise)
2. Accent-folded fallback (if NFC found nothing)
3. Prepend last word of road to city (handles cases where libpostal splits a multi-word city name)

If all matches point to a single country, the pipeline returns immediately. Otherwise, the matches feed into L6.

### L4 — Postal Code Detection

Matches the parsed `postcode` component against country-specific postal code patterns via regex. Unique formats (PL: `NN-NNN`, PT: `NNNN-NNN`, SE: `NNN NN`) resolve to a single country. Ambiguous formats (5-digit, 4-digit) produce a candidate set. The result feeds into L6.

### L5 — Linguistic Features

Detects language-specific address terms in the parsed `road` component (e.g., `straße` → DE/AT, `straat` → NL/BE, `rue` → FR, `rua` → PT). Uses both exact word matching and suffix matching to handle Germanic compound words (e.g., `wiesenstraße` ends with `straße`).

Tries the original text first, then accent-folded as fallback. The result feeds into L6.

### L6 — Voting

Combines all signals from L3 (ambiguous city matches), L4 (postal code), and L5 (linguistic features). Each signal gives +1 vote per country it supports. The country with the most votes wins. Ties return `None`.

## Technology Stack

| Component | Technology |
|---|---|
| HTTP framework | FastAPI + Uvicorn |
| Address parsing | libpostal (via pypostal) |
| City matching | FlashText (trie-based, word-boundary-aware) |
| Text normalization | `unicodedata` (stdlib) |
| Postal code detection | `re` (stdlib) |
| Data models | Pydantic |
| Containerization | Docker |
