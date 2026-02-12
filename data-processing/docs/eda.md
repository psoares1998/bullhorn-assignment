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

### 2.4 Structural Patterns

Address structure varies significantly by country. Sampled distribution (per 1000):

| Pattern | Description | Most Common In |
|---|---|---|
| `plain` | No commas, no postal code | IT (50%), AT/FR/NL/BE (~43%) |
| `comma` | Has commas but no postal code | EE (51%), DE (40%) |
| `comma+postal` | Commas with postal code | AT/BE/NL/FR/SI/SK (~17-19%) |
| `number` | Has numbers but no commas | CZ (50%), SE (18%) |

### 2.5 Non-ASCII Characters

**29.8%** of all addresses (177,349) contain non-ASCII characters (ö, ü, ä, ß, ç, ã, ń, ř, š, etc.). Both normalization and accent-aware matching are required.

---

## 3. City Index Characteristics

### 3.1 Ambiguous Cities

**208 city names** appear in multiple countries. Examples:

| City | Countries | Risk Level |
|---|---|---|
| Halle | BE, DE, NL | High — 3 major countries |
| Brakel | BE, DE, NL | High — 3 major countries |
| Rudno | PL, SI, SK | Medium |
| Strassen | AT, LU | Medium |
| Lans, Vals, Bach | AT, FR | Medium |
| Breznica, Brezovica | SI, SK | Low — similar regions |

**Implication:** City-only matching will misclassify these without a disambiguation mechanism.

### 3.2 Multi-Word City Names

**19,910 cities (25.7%)** contain multiple words. Examples:

- `Polling in Tirol` (AT) — contains the common word "in"
- `Going am Wilden Kaiser` (AT) — 4 words
- `Sas Van Gent` (NL) — contains "Van"
- `St. Anton am Arlberg` (AT) — abbreviation + preposition
- `Harku vald,Vääna-Jõesuu küla,Preeria aiandusühistu` (EE) — compound administrative name

**Implication:** Simple token-based lookup fails entirely for these. Substring or multi-token matching is required, with longest-match priority.

### 3.3 Very Short City Names

Cities with 1-3 characters exist and pose a false-positive risk:

| City | Country | Risk |
|---|---|---|
| `Y` | FR | Matches inside many words |
| `Erl`, `Rum` | AT | Common substrings |
| `Gaj` | PL, SI | Short + ambiguous |
| `Lom` | CZ, SI | Short + ambiguous |
| `Vir` | SI | Short |
| `Col` | SI | Common English word |

**Implication:** Short city names require boundary-aware matching (word boundaries, not substring).

### 3.4 Non-ASCII City Names

**25.3%** of city names (19,625) contain non-ASCII characters:
- German: `ö, ü, ä, ß` (Kitzbühel, Großglockner)
- French: `é, è, ê, ç, ô` (Orléans)
- Polish: `ń, ś, ź, ż, ł, ó` (Oleśnica)
- Czech/Slovak: `ř, ž, š, č, ů` (Plešivec)
- Estonian: `ä, ö, ü, õ` (Vääna-Jõesuu)
- Portuguese: `ã, õ, ç, á, ê`

**Implication:** Matching must handle both the accented and potentially unaccented forms.

---

## 4. Key Challenges and Edge Cases

### 4.1 Estonian Address Structure

Estonian addresses use a distinct administrative hierarchy with comma-separated components:

```
Kohila Vald,Kohila Alev
rae vald,lagedi alevik
Harku vald,Vääna-Jõesuu küla,Preeria aiandusühistu
```

Terms like `vald` (municipality), `küla` (village), `alevik` (borough), `linn` (city) are structural markers, not part of the city name in other countries. This is a **strong linguistic signal** for EE.

### 4.2 Slovenian Bilingual Addresses

Slovenian addresses near the Italian border use bilingual notation with slashes:

```
DREVORED 1.MAJA / VIALE I MAGGIO IZOLA / ISOLA
goriška ulica / vicolo gorizia izola / isola
```

The slash pattern with Italian/Slovenian parallel names is a **distinctive SI indicator**.

### 4.3 Addresses with Minimal Information

| Type | Count | Example |
|---|---|---|
| Single word | ~thousands | `FULPMES`, `völs` |
| Starting with comma | ~dozens | `, KALMAR`, `, Arby` |
| Very short (<=3 chars) | 451 | `ERL`, `RUM`, `råå` |
| Only postal code + city | ~thousands | `6130, Schwaz` |

These rely entirely on city matching for classification.

### 4.4 Encoding Artifacts

Some addresses contain encoding issues:

```
Rue De La Mosquã©E (Mamoudzou)   — "ã©" should be "é"
```

Robust normalization should account for common UTF-8 decoding artifacts.

---

## 5. Design Implications

| Observation | Implication |
|---|---|
| 33/33/33 case split | Case-insensitive normalization is mandatory |
| ~29% have explicit country name | First-priority check — highest confidence signal |
| NL/PL postal codes are unique | Postal code regex can resolve these countries directly |
| 208 ambiguous cities | Disambiguation layer required (postal code, linguistic features, context) |
| 25.7% multi-word cities | Token-based lookup insufficient — need substring/multi-token matching |
| Short city names (1-3 chars) | Word-boundary-aware matching to avoid false positives |
| 30% non-ASCII characters | Accent-aware normalization (both index and query) |
| EE/SI have distinct structures | Linguistic markers (`vald`, `küla`, `/` bilingual) serve as country signals |
| Language-specific street terms | `straße` → DE/AT, `straat` → NL/BE, `rue` → FR/BE/LU, `rua` → PT — useful as tiebreakers |
| Romania has 5 cities | Supplementary data needed for production coverage |
